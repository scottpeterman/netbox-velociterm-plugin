# Installation Guide for Your NetBox Docker Setup

## Your Environment
- **Location**: `~/netbox-dev/netbox-docker`
- **NetBox**: Running in Docker container
- **VelociTerm**: Running on WSL2 (port 3000)

## Step 1: Copy Plugin to NetBox Docker

```bash
cd ~/netbox-dev/netbox-docker

# Create plugins directory if it doesn't exist
mkdir -p plugins

# Copy the plugin (adjust source path as needed)
cp -r /path/to/netbox-deviceterm-plugin plugins/netbox-deviceterm
```

## Step 2: Mount Plugin in Docker

Edit `~/netbox-dev/netbox-docker/docker-compose.override.yml`:

Add or update the netbox service volumes:

```yaml
services:
  netbox:
    volumes:
      - ./plugins/netbox-deviceterm:/opt/netbox-deviceterm:ro
```

If the file doesn't exist, create it:

```yaml
version: '3.4'
services:
  netbox:
    volumes:
      - ./plugins/netbox-deviceterm:/opt/netbox-deviceterm:ro
```

## Step 3: Install Plugin in Container

```bash
cd ~/netbox-dev/netbox-docker

# Restart to mount the volume
docker compose restart netbox

# Wait a few seconds
sleep 5

# Install the plugin
docker compose exec netbox pip install /opt/netbox-deviceterm

# Verify installation
docker compose exec netbox pip list | grep netbox-deviceterm
```

Expected output:
```
netbox-deviceterm    0.1.0
```

## Step 4: Configure the Plugin

Edit `~/netbox-dev/netbox-docker/configuration/plugins.py`:

```python
# If file doesn't exist, create it
# Add or update these sections:

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
```

**Note**: `host.docker.internal` is a special DNS name that Docker uses to reach the WSL2 host.

## Step 5: Restart NetBox

```bash
cd ~/netbox-dev/netbox-docker
docker compose restart netbox

# Watch logs to ensure it starts properly
docker compose logs netbox -f
```

Look for any errors. Press Ctrl+C to exit logs when you see NetBox is running.

## Step 6: Verify Installation

```bash
# Check if plugin is loaded
docker compose exec netbox python /opt/netbox/netbox/manage.py shell

# In the Python shell:
>>> from django.conf import settings
>>> print('netbox_deviceterm' in settings.PLUGINS)
True
>>> print(settings.PLUGINS_CONFIG.get('netbox_deviceterm'))
{'terminal_scheme': 'http', 'terminal_host': 'host.docker.internal', 'terminal_port': '3000', 'ssh_port': '22'}
>>> exit()
```

## Step 7: Test in NetBox

1. Open NetBox in browser: `http://localhost:8000`
2. Login with your credentials 
3. Navigate to: **Devices** → Select any device (e.g., T1000)
4. Look for **Terminal** button in the top-right area
5. Click the button
6. New tab should open with VelociTerm embedded

Expected URL format:
```
http://host.docker.internal:3000/embed/?host=10.0.0.108&port=22&name=T1000&bep=3000
```

## Troubleshooting

### Terminal Button Not Showing

```bash
# Clear NetBox cache
docker compose exec netbox python /opt/netbox/netbox/manage.py clearcache

# Restart services
docker compose restart netbox netbox-worker

# Check logs for errors
docker compose logs netbox | grep -i error
```

### VelociTerm Not Loading

```bash
# Test connectivity from NetBox container to VelociTerm
docker compose exec netbox curl -v http://host.docker.internal:3000/embed/

# If this fails, try alternative:
docker compose exec netbox curl -v http://172.17.0.1:3000/embed/
```

If `host.docker.internal` doesn't work, update your config to use the Docker bridge IP:

```python
'terminal_host': '172.17.0.1',  # or '172.18.0.1'
```

### Find Docker Bridge IP

```bash
# Get Docker bridge gateway IP
ip route | grep docker0 | awk '{print $9}'
```

### VelociTerm Must Bind to 0.0.0.0

Make sure VelociTerm is listening on all interfaces:

```python
# In VelociTerm startup code
app.run(host='0.0.0.0', port=3000)  # ✓ Correct

# NOT:
app.run(host='127.0.0.1', port=3000)  # ✗ Won't work from Docker
```

Test from WSL2:
```bash
# Should work
curl http://localhost:3000/embed/

# Also should work (your WSL2 IP)
curl http://$(hostname -I | awk '{print $1}'):3000/embed/
```

## Common Commands

```bash
# Reinstall plugin
docker compose exec netbox pip uninstall netbox-deviceterm -y
docker compose exec netbox pip install /opt/netbox-deviceterm
docker compose restart netbox

# View logs
docker compose logs netbox -f

# Clear cache
docker compose exec netbox python /opt/netbox/netbox/manage.py clearcache

# Check plugin status
docker compose exec netbox pip show netbox-deviceterm
```

## Next Steps

1. Ensure all your devices have primary IPs set in NetBox
2. Test terminal connections to multiple devices
3. Configure VelociTerm authentication if needed
4. Consider HTTPS setup for production use

## Quick Test Checklist

- [ ] Plugin installed: `pip list | grep netbox-deviceterm`
- [ ] Plugin in PLUGINS list in configuration/plugins.py
- [ ] PLUGINS_CONFIG set correctly
- [ ] NetBox restarted after configuration
- [ ] VelociTerm running on WSL2
- [ ] VelociTerm accessible: `curl http://localhost:3000`
- [ ] VelociTerm binding to 0.0.0.0
- [ ] Terminal button appears on device page
- [ ] Clicking button opens VelociTerm embed
- [ ] Device has primary IP configured

## Support
