from simian.gui import Form, component, utils
from simian.comfy import convert_api_to_app, LOCATIONS


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
        RunWorkflow=mock_workflow,
    )
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def mock_workflow(_meta_data: dict, payload: dict) -> dict:
    """RunWorkflow callback - mocked as we cannot guarantee that the correct nodes and hardware are available."""
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

        # Recreate the app, but without the File component.
        form = Form(from_file=__file__)
        form.components.pop(-1)

        try:
            # Try to add the workflow WebApp API controls to the app.
            convert_api_to_app(form)

            # Put the updated form in the payload and mark the app to be updated.
            payload["updateForm"] = True
            payload["form"] = form

        except Exception:
            utils.addAlert(
                payload,
                "Could not create ComfyUI WebApp from JSON file. Does it contain WebApp API nodes?",
                "danger",
            )

    return payload
