from django.shortcuts import render, get_object_or_404
from dcim.models import Device
from django.conf import settings
from urllib.parse import urlencode

def device_terminal_view(request, pk):
    """
    Display an embedded VelociTerm terminal iframe for a specific device.
    
    URL format: http://host.docker.internal:3000/embed/?host=10.0.0.108&port=22&name=T1000&bep=3000
    """
    device = get_object_or_404(Device, pk=pk)
    
    # Get plugin configuration
    plugin_config = settings.PLUGINS_CONFIG.get('netbox_deviceterm', {})
    terminal_scheme = plugin_config.get('terminal_scheme', 'http')
    terminal_host = plugin_config.get('terminal_host', 'host.docker.internal')
    terminal_port = plugin_config.get('terminal_port', '3000')
    ssh_port = plugin_config.get('ssh_port', '22')
    
    # Get device IP address - prefer IPv4, fallback to IPv6
    primary_ip = device.primary_ip4 or device.primary_ip6
    
    if primary_ip:
        host_ip = str(primary_ip.address.ip)
    else:
        # Fallback to device name if no IP configured
        host_ip = device.name
    
    # Build VelociTerm embed URL with query parameters
    params = {
        'host': host_ip,
        'port': ssh_port,
        'name': device.name,
        'bep': terminal_port
    }
    
    iframe_url = f"{terminal_scheme}://{terminal_host}:{terminal_port}/embed/?{urlencode(params)}"
    
    context = {
        'device': device,
        'iframe_url': iframe_url,
        'host_ip': host_ip,
    }
    
    return render(request, 'netbox_deviceterm/device_terminal.html', context)
