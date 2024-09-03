import json
import os
from datetime import datetime

import json2html
import plotly.express as px
import requests
from skimage import data

from simian.gui import Form, component, utils

if __name__ == "__main__":
    from simian.local import Uiformio

    Uiformio("hello_world_with_coffee", window_title="Hello World")


def gui_init(meta_data: dict) -> dict:
    # Get application data containing secrets and configurables (local mode).
    get_application_data(meta_data)

    # Create the form and load the json builder into it.
    Form.componentInitializer(app_pic_hello_world=init_app_toplevel_pic)

    form = Form(from_file=__file__)
    examples_url = "https://github.com/Simian-Web-Apps/Python-Examples/"
    payload = {
        "form": form,
        "navbar": {
            "title": (
                f'<a class="text-white" href="{examples_url}" target="_blank">'
                '<i class="fa fa-github"></i></a>&nbsp;Hello World'
            )
        },
        "showChanged": False,
    }

    return payload


def init_app_toplevel_pic(comp: component.HtmlElement):
    # Voeg depictie met titel toe in de linker bovenhoek.
    comp.setLocalImage(
        os.path.join(os.path.dirname(__file__), "app_pic.png"), scale_to_parent_width=True
    )
    comp.customClass = "px-5"


def get_application_data(meta_data: dict):
    # In local mode, add application_data from file.
    # In deployed mode, this informtion is set in App config in Simian Portal.
    if meta_data["mode"] == "local":
        application_data_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "local_application_data.json"
        )

        if os.path.isfile(application_data_file):
            with open(application_data_file) as f:
                meta_data["application_data"] = json.load(f)
        else:
            raise Exception(
                'No file "local_application_data.json" exists. Please copy or remame '
                '"local_application_data.json.sample" to "local_application_data.json", and '
                "edit to set your Wikimedia API key from https://api.wikimedia.org/wiki/Getting_started_with_Wikimedia_APIs."
            )


def gui_event(meta_data: dict, payload: dict) -> dict:
    # Get application data containing secrets and configurables (local mode).
    get_application_data(meta_data)

    Form.eventHandler(coffee_button=get_coffee)
    Form.eventHandler(history_button=get_history)
    callback = utils.getEventFunction(meta_data, payload)

    return callback(meta_data, payload)


def get_coffee(meta_data: dict, payload: dict) -> dict:
    coffee_drawing_obj, _ = utils.getSubmissionData(payload, "coffee_drawing")
    image_coffee = data.coffee()
    coffee_drawing_obj.figure = px.imshow(image_coffee)
    coffee_drawing_obj.figure.update_layout(coloraxis_showscale=False)
    coffee_drawing_obj.figure.update_xaxes(showticklabels=False, ticks="inside")
    coffee_drawing_obj.figure.update_yaxes(showticklabels=False, ticks="inside")
    payload, _ = utils.setSubmissionData(payload, "coffee_drawing", coffee_drawing_obj)

    return payload


def get_history(meta_data: dict, payload: dict) -> dict:
    selectedDate, _ = utils.getSubmissionData(payload, "dateTime")

    if not selectedDate:
        payload, _ = utils.setSubmissionData(payload, "appmessages", "Select a date first.")
        return payload

    selectedDate = selectedDate.split("T")
    selectedDate = datetime.strptime(selectedDate[0], "%Y-%m-%d").date().strftime("%m/%d")
    url = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/" + selectedDate
    headers = {
        "Authorization": "Bearer " + meta_data["application_data"]["wikimedia_service_api_key"],
        "User-Agent": meta_data["application_data"]["wikimedia_service_user_agent"],
    }

    response = requests.get(url, headers=headers)
    datajson = response.json()

    yearitems = [item["year"] for item in datajson["events"]]
    eventitems = [": " + item["text"] for item in datajson["events"]]
    summaryitems = [f"{x[0]}{x[1]}" for x in zip(yearitems, eventitems)]
    datahtml_obj = json2html.Json2Html()
    datahtml = datahtml_obj.convert(json=summaryitems)

    payload, _ = utils.setSubmissionData(payload, "appmessages", "Selected date: " + selectedDate)
    payload, _ = utils.setSubmissionData(payload, "historylisting", datahtml)

    return payload
