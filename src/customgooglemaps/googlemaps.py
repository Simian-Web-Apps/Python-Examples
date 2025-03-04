import json
from os import path

from simian.gui import Form, component, component_properties, utils  # noqa: F401

cities = {
    "amsterdam": {"lat": 52.3676, "lng": 4.9041},
    "munich": {"lat": 48.1293954, "lng": 11.556663},
    "sydney": {"lat": -33.865143, "lng": 151.209900},
}

# Run this file locally
if __name__ == "__main__":
    import simian.local

    simian.local.Uiformio("googlemaps", window_title="Google Maps", debug=True, show_refresh=True)


def gui_init(meta_data: dict) -> dict:
    """Create a form and set a logo and title."""

    # Get application data containing secrets and configurables (local mode).
    get_application_data(meta_data)

    # Create form.
    form = Form()

    # Add custom javascript and insert api key from application data
    file_path = path.join(path.dirname(path.abspath(__file__)), "custom-js", "init.js")
    with open(file_path, "r") as file:
        file_content = file.read()

    for key in ["google_maps_frontend_api_key", "google_maps_map_name", "google_maps_map_mapid"]:
        file_content = file_content.replace(
            "[" + key + "]",
            meta_data["application_data"][key],
        )
    form.addCustomJavaScript(file_content)

    # Base payload
    examples_url = "https://github.com/Simian-Web-Apps/Python-Examples/"

    payload = {
        "form": form,
        "navbar": {
            "title": (
                f'<a class="text-white" href="{examples_url}" target="_blank">'
                '<i class="fa fa-github"></i></a>&nbsp;&nbsp;Google Maps API PoC'
            )
        },
        "showChanged": True,
    }

    # Hidden component to store
    LatLng = component.Hidden("latlng", form)
    LatLng.defaultValue = "sydney"

    Markers = component.Hidden("markers", form)
    Markers.defaultValue = [{"lat": -33.865143, "lng": 151.209900}]

    Centers = component.Hidden("centers", form)
    Centers.defaultValue = cities

    container = component.Container("container", form)
    container.addCustomClass("container")

    htmlMap = component.HtmlElement("google_maps_html", container)
    htmlMap.tag = "div"
    htmlMap.setAttrs(
        ["name", "style"],
        [meta_data["application_data"]["google_maps_map_name"], "height:50vh; min-height: 10em;"],
    )
    htmlMap.addCustomClass("mb-3", "bg-light", "w-100")
    htmlMap.calculateValue = "updateMap();"

    addMarkersOnClickToggle = component.Toggle("add_marker_on_click_toggle")
    addMarkersOnClickToggle.label = "Add marker on map-click"
    addMarkersOnClickToggle.hideLabel = True
    addMarkersOnClickToggle.defaultValue = False
    addMarkersOnClickToggle.leftLabel = "Markers"
    addMarkersOnClickToggle.rightLabel = ""

    cityButtons = []
    for city in cities:
        cityButton = component.Button("button_" + city)
        cityButton.addCustomClass("btn-block")
        cityButton.label = city.capitalize()
        cityButton.setEvent(city)
        cityButtons.append(cityButton)

    cols = component.Columns("columns", container)
    cols.setContent([addMarkersOnClickToggle] + cityButtons, [3, 3, 3, 3])

    purgeMarkerButton = component.Button("purge_marker_button", container)
    purgeMarkerButton.label = "Purge Last Added Marker"
    purgeMarkerButton.addCustomClass("btn-block btn-danger")
    purgeMarkerButton.action = "custom"
    purgeMarkerButton.custom = "purgeMarker(); data['markers'].pop();"

    htmlMarkers = component.HtmlElement("google_maps_markers_html", container)
    htmlMarkers.tag = "pre"
    htmlMarkers.addCustomClass("bg-light", "px-1", "pt-1")
    htmlMarkers.setAttrs(["style"], ["height:4rem;"])
    htmlMarkers.content = "{{stringifyMarkers(data['markers'])}}"
    htmlMarkers.refreshOnChange = True

    # payload["pristine"] = True

    return payload


def gui_event(meta_data: dict, payload: dict) -> dict:
    # set the Form.eventHandler for each city in cities as
    # Form.eventHandler(amsterdam=setCenter("amsterdam"))
    for key in cities.keys():
        Form.eventHandler(**{key: setCenter(key)})

    callback = utils.getEventFunction(meta_data, payload)

    # Remove the "form has changes badge".
    payload["pristine"] = True

    return callback(meta_data, payload)


def setCenter(latlng: dict) -> callable:
    def inner(meta_data: dict, payload: dict) -> dict:
        utils.setSubmissionData(payload, "latlng", latlng)
        return payload

    return inner


def get_application_data(meta_data: dict):
    """In local mode add application_data from file."""

    # In deployed mode this informtion is set on App config in Simian Portal
    if meta_data["mode"] == "local":
        application_data_file = path.join(
            path.dirname(path.realpath(__file__)), "local_application_data.json"
        )

        if path.isfile(application_data_file):
            with open(application_data_file) as f:
                meta_data["application_data"] = json.load(f)
        else:
            raise Exception(
                'No file "local_application_data.json" exists. Please copy or remame '
                '"local_application_data.json.sample" to "local_application_data.json", and '
                "edit to set application data such as API keys."
            )
