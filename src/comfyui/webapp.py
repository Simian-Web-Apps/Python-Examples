"""Simian-ComfyUI webapps example."""

from simian.comfy.examples.compositemasked.comfy_app import gui_event as gui_event
from simian.comfy.examples.compositemasked.comfy_app import gui_init as gui_init_app
from simian.gui import component


def gui_init(meta_data):
    """Simian-ComfyUI example app extension adding a description."""
    form_dict = gui_init_app(meta_data)

    descr_panel = component.Panel("descr")
    descr_panel.label = "Description"
    descr_panel.collapsible = True
    descr_panel.collapsed = True

    description = component.HtmlElement("description", descr_panel)
    description.label = "Description"
    description.content = """This example shows the Simian-ComfyUI `compositemasked` example.
<br/><br/>
In ComfyUI a simple image composition workflow was extended with WebApp API nodes. These nodes describe what inputs should be available in the app and with what constraints. `https://github.com/MonkeyProof-Solutions-BV/ComfyUI_webapp`
<br/><br/>
The Simian-ComfyUI-WebApps library has converted these workflow nodes into this app. `https://github.com/Simian-Web-Apps/Simian-ComfyUI-WebApps`
"""

    form_dict["form"].components.insert(0, descr_panel)

    return form_dict
