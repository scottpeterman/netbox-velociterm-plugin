# NetBox Docker Plugin Installation - Troubleshooting Guide

This guide documents the real-world challenges and solutions encountered when installing the NetBox VelociTerm plugin in a Docker environment.

## The Docker Dance: What We Learned

Installing NetBox plugins in Docker is different from bare-metal installations. Here's everything we encountered and how to solve it.

---

## Issue 1: Finding the Right Python/pip

### Problem
Standard `pip` commands don't work in the NetBox container:

```bash
docker compose exec netbox pip install /opt/netbox-deviceterm
# Error: pip: command not found
```

### Why This Happens
- The NetBox container doesn't have `pip` in the default PATH
- NetBox uses a Python virtual environment at `/opt/netbox/venv`
- The container runs as user `unit` (uid 999), not root

### Solutions (in order of what we tried)

#### ❌ Attempt 1: Regular pip
```bash
docker compose exec netbox pip install /opt/netbox-deviceterm
# Result: pip: command not found
```

#### ❌ Attempt 2: Full path to venv pip
```bash
docker compose exec netbox /opt/netbox/venv/bin/pip install /opt/netbox-deviceterm
# Result: /opt/netbox/venv/bin/pip: no such file or directory
```

#### ❌ Attempt 3: Python module method
```bash
docker compose exec netbox python3 -m pip install /opt/netbox-deviceterm
# Result: No module named pip
```

#### ✅ Solution: Use uv (NetBox's package manager)
```bash
docker compose exec netbox /usr/local/bin/uv pip install /opt/netbox-deviceterm
```

**Key Discovery:** Modern NetBox Docker images use `uv` (a fast Python package manager) instead of traditional pip.

---

## Issue 2: Editable Install Permission Denied

### Problem
Trying to install in editable mode failed with permission errors:

```bash
docker compose exec netbox /usr/local/bin/uv pip install -e /opt/netbox-deviceterm

# Error:
# error: could not create 'netbox_deviceterm.egg-info': Permission denied
```

### Why This Happens
1. Volume mounted as `:ro` (read-only)
2. Editable install needs to create `.egg-info` directory
3. Container user `unit` doesn't have write permissions

### Solution 1: Change Volume Mount
```yaml
# docker-compose.override.yml
volumes:
  - ../netbox-deviceterm-plugin:/opt/netbox-deviceterm:rw  # Changed from :ro
```

### Solution 2: Fix Host Permissions
```bash
# Make plugin directory writable by container user
chmod -R 777 ~/netbox-dev/netbox-deviceterm-plugin
```

---

## Issue 3: Cannot Write to venv

### Problem
Even with correct plugin permissions, installation failed:

```bash
docker compose exec netbox /usr/local/bin/uv pip install /opt/netbox-deviceterm

# Error:
# failed to create directory `/opt/netbox/venv/lib/python3.12/site-packages/netbox_deviceterm`: 
# Permission denied (os error 13)
```

### Why This Happens
The virtual environment `/opt/netbox/venv` is owned by `root`, but the container runs as user `unit`:

```bash
docker compose exec netbox ls -la /opt/netbox/ | grep venv
# drwxr-xr-x  1 root root  4096 Oct 29 05:47 venv

docker compose exec netbox whoami
# unit

docker compose exec netbox id
# uid=999(unit) gid=0(root) groups=0(root)
```

### ✅ Solution: Install as Root
```bash
docker compose exec -u root netbox /usr/local/bin/uv pip install /opt/netbox-deviceterm
```

**This is the key command that works!**

---

## Complete Installation Procedure

### Step 1: Prepare Plugin Directory
```bash
cd ~/netbox-dev
tar -xzf netbox-deviceterm-plugin.tar.gz

# Fix permissions so container can read/write
chmod -R 777 netbox-deviceterm-plugin
```

### Step 2: Update docker-compose.override.yml
```yaml
services:
  netbox:
    ports:
      - "8000:8080"
    environment:
      DEVELOPER: 'true'
      DEBUG: 'true'
    volumes:
      - ../netbox-deviceterm-plugin:/opt/netbox-deviceterm:rw
```

### Step 3: Restart NetBox
```bash
cd ~/netbox-dev/netbox-docker
docker compose down
docker compose up -d
```

### Step 4: Install Plugin (as root)
```bash
docker compose exec -u root netbox /usr/local/bin/uv pip install /opt/netbox-deviceterm
```

Expected output:
```
Using Python 3.12.3 environment at: /opt/netbox/venv
Resolved 1 package in 1.69s
      Built netbox-deviceterm @ file:///opt/netbox-deviceterm
Prepared 1 package in 329ms
Installed 1 package in 4ms
 + netbox-deviceterm==0.1.0 (from file:///opt/netbox-deviceterm)
```

### Step 5: Verify Installation
```bash
docker compose exec netbox /usr/local/bin/uv pip list | grep deviceterm
# Output: netbox-deviceterm             0.1.0
```

### Step 6: Configure Plugin
```bash
# Edit configuration/plugins.py
cat > ~/netbox-dev/netbox-docker/configuration/plugins.py << 'EOF'
PLUGINS = [
    'netbox_deviceterm',
]

PLUGINS_CONFIG = {
    'netbox_deviceterm': {
        'terminal_scheme': 'http',
        'terminal_host': 'host.docker.internal',
        'terminal_port': '3000',
        'ssh_port': '22',
    }
}
EOF
```

### Step 7: Restart NetBox Again
```bash
docker compose restart netbox
```

### Step 8: Verify Plugin Loaded
```bash
docker compose exec netbox python /opt/netbox/netbox/manage.py shell

>>> from django.conf import settings
>>> print('netbox_deviceterm' in settings.PLUGINS)
True
>>> print(settings.PLUGINS_CONFIG.get('netbox_deviceterm'))
{'terminal_scheme': 'http', 'terminal_host': 'host.docker.internal', ...}
>>> exit()
```

---

## Common Errors and Solutions

### Error: "pip: command not found"
**Solution:** Use `/usr/local/bin/uv pip` instead of `pip`

### Error: "Permission denied" during install
**Solution:** Use `docker compose exec -u root` to run as root

### Error: "Read-only file system" 
**Solution:** Change volume mount from `:ro` to `:rw` in docker-compose.override.yml

### Error: Plugin not in PLUGINS list
**Solution:** Check that `configuration/plugins.py` exists and is mounted into container:
```bash
docker compose exec netbox cat /etc/netbox/config/plugins.py
```

### Error: "host.docker.internal" not resolving
**Solution:** Use Docker bridge IP instead:
```bash
# Find bridge IP
ip route | grep docker0 | awk '{print $9}'

# Update plugins.py with actual IP (e.g., 172.17.0.1)
'terminal_host': '172.17.0.1',
```

---

## Development Workflow

### Making Changes to Plugin Code

Since the plugin is volume-mounted, you can edit locally and reinstall:

```bash
# 1. Edit files in ~/netbox-dev/netbox-deviceterm-plugin/

# 2. Reinstall plugin
docker compose exec -u root netbox /usr/local/bin/uv pip install --force-reinstall /opt/netbox-deviceterm

# 3. Restart NetBox
docker compose restart netbox

# 4. Test changes
```

### For Faster Iteration

If you're making frequent changes:

```bash
# Install in editable mode (after fixing permissions)
docker compose exec -u root netbox /usr/local/bin/uv pip install -e /opt/netbox-deviceterm

# Now you only need to restart, not reinstall
docker compose restart netbox
```

---

## Understanding NetBox Docker User Permissions

### The Container User
```bash
docker compose exec netbox id
# uid=999(unit) gid=0(root) groups=0(root)
```

The NetBox container runs as user `unit` (uid 999) for security, but:
- The venv is owned by `root`
- Plugin installation requires root access
- Volume mounts use host user permissions

### Why We Need Root for Installation

```
Host Machine (your user)
  ↓
Docker Volume Mount
  ↓  
Container (runs as 'unit')
  ↓
/opt/netbox/venv (owned by 'root')
```

To install packages in the venv, we need root access in the container.

### Is This Safe?

Yes! Using `-u root` only affects the container, not your host system:
- Root in container ≠ root on host
- Confined by Docker security
- Standard practice for package installation
- Container is ephemeral

---

## Verification Checklist

After installation, verify everything works:

- [ ] Plugin shows in pip list: `docker compose exec netbox /usr/local/bin/uv pip list | grep deviceterm`
- [ ] Plugin in NetBox system: Navigate to System → Plugins
- [ ] Plugin config loaded: Check Python shell (see Step 8 above)
- [ ] Terminal button appears: Go to any device page
- [ ] Button opens VelociTerm: Click terminal button
- [ ] Connection works: Test SSH to a device

---

## Network Configuration for VelociTerm

### Docker DNS Names

In Docker, `host.docker.internal` is a special DNS name that resolves to the host machine:

```yaml
PLUGINS_CONFIG = {
    'netbox_deviceterm': {
        'terminal_host': 'host.docker.internal',  # Reaches WSL2/host
        'terminal_port': '3000',
    }
}
```

### Testing Connectivity

From inside the container:
```bash
# Test if VelociTerm is reachable
docker compose exec netbox curl -v http://host.docker.internal:3000/embed/
```

If that fails, try:
```bash
# Use Docker bridge IP
docker compose exec netbox curl -v http://172.17.0.1:3000/embed/
```

### VelociTerm Must Bind to 0.0.0.0

**Critical:** VelociTerm must listen on all interfaces, not just localhost:

```python
# VelociTerm startup - CORRECT
app.run(host='0.0.0.0', port=3000)

# NOT THIS - won't work from Docker
app.run(host='127.0.0.1', port=3000)
```

Verify VelociTerm is listening correctly:
```bash
# On WSL2 host
netstat -tlnp | grep 3000
# Should show: 0.0.0.0:3000, not 127.0.0.1:3000
```

---

## Summary: The Complete Docker Dance

1. **Extract plugin** to directory accessible from Docker
2. **Fix permissions** with `chmod -R 777`
3. **Mount as volume** in docker-compose.override.yml (`:rw`)
4. **Install as root** using `/usr/local/bin/uv pip`
5. **Configure plugin** in `configuration/plugins.py`
6. **Restart NetBox** to load configuration
7. **Verify** installation through UI and CLI

The key insights:
- NetBox Docker uses `uv`, not regular `pip`
- Installation requires root in container
- Plugin directory needs write permissions for editable installs
- VelociTerm must bind to `0.0.0.0`, not `127.0.0.1`
- `host.docker.internal` is your friend in Docker networking

---

## Quick Reference Commands

```bash
# Install plugin (most important command!)
docker compose exec -u root netbox /usr/local/bin/uv pip install /opt/netbox-deviceterm

# Verify installation
docker compose exec netbox /usr/local/bin/uv pip list | grep deviceterm

# Check configuration loaded
docker compose exec netbox python /opt/netbox/netbox/manage.py shell

# View logs
docker compose logs netbox -f

# Restart after changes
docker compose restart netbox

# Complete restart
docker compose down && docker compose up -d

# Test VelociTerm connectivity
docker compose exec netbox curl http://host.docker.internal:3000/embed/
```

---

## When Things Go Wrong

### Start Over from Clean State

```bash
cd ~/netbox-dev/netbox-docker

# Stop everything
docker compose down

# Remove any failed installations
docker compose exec -u root netbox /usr/local/bin/uv pip uninstall netbox-deviceterm -y

# Clear Python cache
docker compose exec netbox find /opt/netbox-deviceterm -name "*.pyc" -delete
docker compose exec netbox find /opt/netbox-deviceterm -name "__pycache__" -delete

# Start fresh
docker compose up -d

# Reinstall
docker compose exec -u root netbox /usr/local/bin/uv pip install /opt/netbox-deviceterm
docker compose restart netbox
```

---

## Success Indicators

You know it's working when:

✅ Plugin shows in System → Plugins → Installed Plugins  
✅ "Terminal" button appears on device pages  
✅ Clicking button opens new tab with VelociTerm  
✅ VelociTerm shows authentication dialog  
✅ After auth, SSH terminal connects to device  

---

## Getting Help

If you're still stuck:

1. Check NetBox logs: `docker compose logs netbox | grep -i error`
2. Verify file exists: `docker compose exec netbox ls -la /opt/netbox-deviceterm/`
3. Check config: `docker compose exec netbox cat /etc/netbox/config/plugins.py`
4. Test connectivity: `docker compose exec netbox curl http://host.docker.internal:3000`
5. Review this guide from the top - we probably covered your issue!

---

*This guide represents the actual troubleshooting journey of installing a NetBox plugin in Docker. Every error message and solution was tested and verified.*