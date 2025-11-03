from netbox.plugins import PluginConfig

class DeviceTermConfig(PluginConfig):
    name = 'netbox_deviceterm'
    verbose_name = 'Device Terminal (VelociTerm)'
    description = 'Embed VelociTerm SSH terminal for devices'
    version = '0.1.0'
    author = 'Scott Peterman'
    author_email = 'scottpeterman@gmail.com'
    base_url = 'deviceterm'
    required_settings = []
    default_settings = {
        'terminal_scheme': 'http',
        'terminal_host': 'host.docker.internal',
        'terminal_port': '3000',
        'ssh_port': '22',
    }

config = DeviceTermConfig
