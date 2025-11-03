from netbox.plugins import PluginTemplateExtension
from django.urls import reverse

class DeviceTerminalButton(PluginTemplateExtension):
    """
    Add a "Terminal" button to device detail pages in NetBox.
    """
    model = 'dcim.device'

    def buttons(self):
        device = self.context['object']
        terminal_url = reverse('plugins:netbox_deviceterm:device_terminal', kwargs={'pk': device.pk})
        
        return f'''
        <a href="{terminal_url}" class="btn btn-sm btn-primary" target="_blank">
            <i class="mdi mdi-console"></i> Terminal
        </a>
        '''

template_extensions = [DeviceTerminalButton]
