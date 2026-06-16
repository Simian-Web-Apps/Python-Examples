import logging
import traceback

from simian.gui import Form, component, utils, internal
from simian.comfy import convert_api_to_app, LOCATIONS
from simian.comfy.examples.compositemasked.comfy_app import gui_event as gui_event_app


def gui_init(_meta_data: dict) -> dict:
    # Create the form and load the json builder into it.
    form = Form(from_file=__file__)

    placeholder = component.HtmlElement("placeholder", form)
    placeholder.content = "<br/><br/><br/>-- Placeholder --"

    return {
        "form": form,
        "navbar": {"title": "Simian ComfyUI", "subtitle": "<small>Workflow API mockup app</small>"},
    }


def gui_event(meta_data: dict, payload: dict) -> dict:
    Form.eventHandler(
        WorkflowUploaded=process_workflow,
        RunWorkflow=perform_workflow,
    )
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def perform_workflow(meta_data: dict, payload: dict) -> dict:
    """RunWorkflow callback - mocked when no ComfyUI Server configured, run otherwise."""
    if "COMFY_SERVER" in meta_data["application_data"]:
        gui_event_app(meta_data, payload)
    else:
        utils.addAlert(
            payload,
            "The ComfyUI workflow cannot be run from this app. This is purely an app mockup.",
            "info",
        )
    return payload


def process_workflow(meta_data: dict, payload: dict) -> dict:
    """WorkflowUploaded callback."""
    # Get the workflow API .JSON file.
    payload, file_paths = component.File.storeUploadedFiles(
        meta_data, payload, "comfyUiWorkflowFile"
    )

    if len(file_paths) > 0:
        # A workflow API file has been selected. Try to process it.
        LOCATIONS["workflow"] = file_paths[0]

        # Ensure the Component config is updated before we create any new components.
        mode = meta_data.get("mode", "deployed")
        component.Component._init_config(
            ["mode", "portalCache"], [mode, internal._using_portal_cache(meta_data)]
        )

        # Recreate the app, but without the File component.
        form = Form(from_file=__file__)
        form.components.pop(-1)

        try:
            # Try to add the workflow WebApp API controls to the app.
            convert_api_to_app(form)

            # Put the updated form in the payload and mark the app to be updated.
            payload["updateForm"] = True
            payload["form"] = form
            internal.setCache(meta_data, "formMap", internal.getFormStruct(meta_data, payload))

        except Exception as exc:
            utils.addAlert(
                payload,
                "Could not create ComfyUI WebApp from JSON file. Does it contain WebApp API nodes?",
                "danger",
            )
            logging.debug(traceback.print_tb(exc.__traceback__))

    return payload
