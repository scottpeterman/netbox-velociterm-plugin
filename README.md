# NetBox Device Terminal Plugin (VelociTerm)

Embeds VelociTerm SSH terminal directly into NetBox device pages.

## Features
- Adds "Terminal" button to device detail pages
- Auto-connects using device's primary IP
- Full-screen iframe terminal experience
- Docker-compatible

## Quick Install (Docker)

```bash
# 1. Copy plugin to netbox-docker
cd ~/netbox-dev/netbox-docker
mkdir -p plugins
cp -r /path/to/netbox-deviceterm-plugin plugins/netbox-deviceterm

# 2. Add volume mount to docker-compose.override.yml
services:
  netbox:
    volumes:
      - ./plugins/netbox-deviceterm:/opt/netbox-deviceterm:ro

# 3. Install in container
docker compose exec netbox pip install /opt/netbox-deviceterm

# 4. Configure in configuration/plugins.py
PLUGINS = ['netbox_deviceterm']

PLUGINS_CONFIG = {
    'netbox_deviceterm': {
        'terminal_scheme': 'http',
        'terminal_host': 'host.docker.internal',
        'terminal_port': '3000',
        'ssh_port': '22',
    }
}

# 5. Restart
docker compose restart netbox
```

## Configuration

### Docker Setup (VelociTerm on WSL2 host)
```python
PLUGINS_CONFIG = {
    'netbox_deviceterm': {
        'terminal_scheme': 'http',
        'terminal_host': 'host.docker.internal',  # Special Docker DNS
        'terminal_port': '3000',
        'ssh_port': '22',
    }
}
```

### Remote VelociTerm Server
```python
PLUGINS_CONFIG = {
    'netbox_deviceterm': {
        'terminal_scheme': 'https',
        'terminal_host': '192.168.1.100',
        'terminal_port': '3000',
        'ssh_port': '22',
    }
}
```

## VelociTerm Requirements

VelociTerm MUST bind to 0.0.0.0 (not 127.0.0.1) to be accessible from Docker:

```python
# In VelociTerm startup
app.run(host='0.0.0.0', port=3000)
```

## Usage

1. Navigate to any device in NetBox
2. Click "Terminal" button
3. VelociTerm opens in new tab with device connection

## URL Format

Plugin generates VelociTerm embed URLs:
```
http://host.docker.internal:3000/embed/?host=10.0.0.108&port=22&name=T1000&bep=3000
```

## Troubleshooting

```bash
# Verify plugin installed
docker compose exec netbox pip list | grep netbox-deviceterm

# Check logs
docker compose logs netbox -f

# Test VelociTerm connectivity from container
docker compose exec netbox curl http://host.docker.internal:3000/embed/

# Clear cache
docker compose exec netbox python /opt/netbox/netbox/manage.py clearcache

# Restart
docker compose restart netbox
```

## Requirements
- NetBox 3.0+
- VelociTerm (https://github.com/scottpeterman/velociterm)

## License
Apache 2.0
