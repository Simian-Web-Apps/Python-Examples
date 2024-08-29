import json
import math
import re
import time
from http import HTTPStatus
from os import path

import pandas as pd
import plotly.express as px
import requests
from simian.gui import Form, component, component_properties, utils

# Template syntax helpers for slightly more readable formio template construction using f-strings.
# Avoids having to escape (by doubling them) the many braces used in templates. Some may not be used.
# Start & end scripting block - not displayed
TMPL_SCRIPT_START = "{%"
TMPL_SCRIPT_END = "%}"

# Open & close a script block (flow control)
SCRIPT_BLOCK_OPEN = "{"
SCRIPT_BLOCK_CLOSE = "}"

# Start and end block for displaying formio variables (e.g. data) in page.
TMPL_DISPLAY_DATA_START = "{{"
TMPL_DISPLAY_DATA_END = "}}"

# Run this file locally
if __name__ == "__main__":
    import simian.local

    simian.local.Uiformio("route_planner", window_title="Route planner")


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
                "edit to set your openrouteservice.org API key from https://openrouteservice.org/ ."
            )


def gui_init(meta_data: dict) -> dict:
    """Create a form and set a logo and title."""

    # Get application data containing secrets and configurables (local mode).
    get_application_data(meta_data)
    # Extract info from meta data
    truck_image_base_url = meta_data["application_data"]["truck_image_base_url"]
    here_frontend_autocomplete_delay = (
        meta_data["application_data"]["here_frontend_autocomplete_delay_ms"] / 1000
    )
    here_backend_lookup_interval = (
        meta_data["application_data"]["here_backend_lookup_interval_ms"] / 1000
    )
    here_frontend_api_key = meta_data["application_data"]["here_frontend_api_key"]

    # Create form.
    form = Form()

    # Base payload
    examples_url = "https://github.com/Simian-Web-Apps/Python-Examples/"
    ptv_url = "https://ev-truck-route-planner.myptv.com/"

    payload = {
        "form": form,
        "navbar": {
            "title": (
                f'<a class="text-white" href="{examples_url}" target="_blank">'
                '<i class="fa fa-github"></i></a>&nbsp;EV Truck Route Planner Demo '
                f'(<a class="text-white text-underline" href="{ptv_url}" target="_blank"><u>PTV Group Inspired</u></a>)'
            )
        },
        "showChanged": True,
    }

    # Create two columns and add the truck and route panels to them.
    truck_data = get_truck_data(truck_image_base_url)
    truck_panel = create_truck_panel(truck_data)
    route_panel = create_route_panel(
        here_frontend_autocomplete_delay,
        here_backend_lookup_interval,
        here_frontend_api_key,
    )
    cols = component.Columns("two_columns", form)
    cols.setContent([[truck_panel], [route_panel]], [6, 6])

    return payload


def gui_event(meta_data: dict, payload: dict) -> dict:
    """Process the events."""

    # Get application data containing secrets and configurables (local mode).
    get_application_data(meta_data)
    # Extract info from meta data
    here_backend_lookup_interval = (
        meta_data["application_data"]["here_backend_lookup_interval_ms"] / 1000
    )
    here_backend_api_key = meta_data["application_data"]["here_backend_api_key"]
    open_route_service_api_key = meta_data["application_data"][
        "open_route_service_api_key"
    ]

    if payload["event"] == "calculate":
        # Plotly code throws an error on a mapbox._derived key in plotly submission data
        # coming from frontend, this key seems to only exist after frontend resize.
        # See: https://github.com/plotly/plotly.py/issues/2570#issuecomment-738735816
        # Workaround: remove key from payload
        if "mapbox._derived" in payload["submission"]["data"]["plot"]["layout"]:
            del payload["submission"]["data"]["plot"]["layout"]["mapbox._derived"]

        plot_obj, _ = utils.getSubmissionData(payload, "plot")
        waypoints = utils.getSubmissionData(payload, "waypoints")[0]

        truck = utils.getSubmissionData(payload, "selectTruck")
        range = truck[0]["driveTrain"]["officialRange"]

        locations = []
        if waypoints:
            # select_location values.
            locations = [waypoint["select_location"] for waypoint in waypoints]

        # Should not be possible to submit with less than 2 waypoints from frontend.
        if len(locations) < 2:
            payload = utils.addAlert(
                payload,
                "Cannot compute route, please select at least 2 waypoints (Cities).",
                "danger",
            )
        else:
            here_headers = {
                "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
                "Content-Type": "application/json; charset=utf-8",
            }

            locations_data = []
            for location in locations:
                location_id = location["id"]
                here_call = requests.get(
                    f"https://lookup.search.hereapi.com/v1/lookup?id={location_id}&apiKey={here_backend_api_key}",
                    headers=here_headers,
                )

                if here_call.status_code == HTTPStatus.FORBIDDEN:
                    payload = utils.addAlert(
                        payload,
                        (
                            "Call to here.com forbidden, "
                            f"check API key in application data ({str(here_call.status_code)} - {here_call.reason})."
                        ),
                        "danger",
                    )
                    break
                elif not here_call.status_code == HTTPStatus.OK:
                    payload = utils.addAlert(
                        payload,
                        (
                            "Call to here.com API failed "
                            f"({str(here_call.status_code)} - {here_call.reason})."
                        ),
                        "danger",
                    )
                    break
                else:
                    # Get the route infor from the web call
                    locations_data.append(here_call.json())
                    time.sleep(here_backend_lookup_interval)

            # The route
            route = {}

            if len(locations_data) > 0:
                # Call openrouteservice with waypoints and API key

                lon_latList = list(
                    map(
                        lambda x: [x["position"]["lng"], x["position"]["lat"]],
                        locations_data,
                    )
                )
                call = get_route(
                    lon_latList,
                    open_route_service_api_key,
                )

                if call.status_code == HTTPStatus.FORBIDDEN:
                    payload = utils.addAlert(
                        payload,
                        (
                            "Call to openrouteservice.org forbidden, "
                            f"check API key in application data ({str(call.status_code)} - {call.reason})."
                        ),
                        "danger",
                    )
                elif not call.status_code == HTTPStatus.OK:
                    payload = utils.addAlert(
                        payload,
                        (
                            "Call to openrouteservice.org API failed, "
                            f"try reducing total distance ({str(call.status_code)} - {call.reason})."
                        ),
                        "danger",
                    )
                else:
                    # Get the route infor from the web call
                    route = call.json()

                    # Pass waypoints and route to update the plot.
                    update_plot(plot_obj, locations_data, route)

                    # report distances and number of required charges
                    for idx, waypoint in enumerate(waypoints):
                        if idx == 0:
                            waypoint["legDistance"] = 0
                            waypoint["totalDistance"] = 0
                            waypoint["chargeStops"] = 0
                        else:
                            waypoint["legDistance"] = (
                                route["features"][0]["properties"]["segments"][idx - 1][
                                    "distance"
                                ]
                                / 1000
                            )
                            waypoint["totalDistance"] = (
                                waypoints[idx - 1]["totalDistance"]
                                + waypoint["legDistance"]
                            )
                            #                            waypoint["chargeStops"] = waypoints[idx - 1]["chargeStops"] + math.ceil(
                            #                                waypoint["legDistance"] / range
                            #                            )
                            waypoint["chargeStops"] = math.ceil(
                                waypoint["totalDistance"] / range
                            )

                    # Update the payload with the waypoint info.
                    payload, _ = utils.setSubmissionData(
                        payload, "waypoints", waypoints
                    )

                    # Update the payload with the new values in the Plotly object.
                    payload, _ = utils.setSubmissionData(payload, "plot", plot_obj)

                    # Remove the "form has changes badge".
                    payload["pristine"] = True

    else:
        print(payload["event"])

    return payload


def create_route_panel(
    here_frontend_autocomplete_delay,
    here_backend_lookup_interval,
    here_frontend_api_key,
) -> component.Panel:
    # Create the panel
    route_panel = component.Panel("route_panel")
    route_panel.title = """Route by <a href="https://openrouteservice.org" target="_blank"><u>openrouteservice.org</u></a>"""
    route_panel.collapsible = False

    # Create plot with some initial data.
    plot_obj = component.Plotly("plot", route_panel)
    plot_obj.aspectRatio = 2

    update_plot(plot_obj, [], {})
    # Data grid for waypoints selection and results presentation
    waypoints = component.DataGrid("waypoints", route_panel)
    waypoints.label = "Way points"
    waypoints.hideLabel = True
    waypoints.reorder = True
    waypoints.addCustomClass("table", "table-sm", "route-planner-data-grid")
    waypoints.defaultValue = []
    validate_waypoints = component_properties.Validate(waypoints)
    validate_waypoints.minLength = 2
    validate_waypoints.maxLength = 4
    validate_waypoints.customMessage = "Route must consist of 2, 3, or 4 waypoints."

    # Select component in data grid for waypoint (location) selection.
    # https://formio.github.io/formio.js/app/sandbox is a great place to interactively figure out and test the (data) settings for the select component.
    select_location = component.Select("select_location", waypoints)
    select_location.label = """Location<span class="font-weight-normal"> (by <a class="text-decoration-underline" href="https://here.com" target="_blank">here.com</a>)</span>"""
    select_location.block = (
        True  # Make the button fill the entire horizontal space of the parent.
    )
    select_location.widget = "ChoicesJS"
    select_location.dataSrc = "url"
    select_location.data = dict(
        url="https://autocomplete.search.hereapi.com/v1/autocomplete"
    )
    select_location.valuePoperty = "id"
    select_location.template = "<span>{{ item.title }}</span>"
    select_location.selectValues = "items"
    select_location.searchField = "q"
    select_location.filter = "apiKey=" + here_frontend_api_key
    select_location.limit = 5
    select_location.searchDebounce = here_frontend_autocomplete_delay
    select_location.errorLabel = "Location"
    placeholder = "Type to search"
    if here_frontend_autocomplete_delay:
        placeholder = f"{placeholder} ({here_frontend_autocomplete_delay}s delay)"
    select_location.placeholder = placeholder
    select_location.setRequired()

    # Number component in data grid to display leg distance
    leg_dist = component.Number("legDistance", waypoints)
    leg_dist.label = "Leg (km)"
    leg_dist.decimalLimit = 2
    leg_dist.requireDecimal = True
    leg_dist.delimiter = True
    leg_dist.disabled = True

    # Number component in data grid to display total distance
    total_dist = component.Number("totalDistance", waypoints)
    total_dist.label = "Total (km)"
    total_dist.decimalLimit = 2
    total_dist.requireDecimal = True
    total_dist.delimiter = True
    total_dist.disabled = True

    # Number component in data grid to display total number of charge stops
    charge_stops = component.Number("chargeStops", waypoints)
    charge_stops.label = "Charges (#)"
    charge_stops.decimalLimit = 0
    charge_stops.requireDecimal = False
    charge_stops.delimiter = True
    charge_stops.disabled = True

    # Add rate limit disclaimer only if one of the delays non zero
    if here_frontend_autocomplete_delay or here_backend_lookup_interval:
        rate_limit_disclaimer = component.HtmlElement("rate_disclaimer", route_panel)
        rate_limit_disclaimer.tag = "p"
        rate_limit_disclaimer.content = f"""<small><i class="fa fa-exclamation-circle text-danger"></i> To avoid demo service disruption caused by applicable here.com rate limitations under our plan, delays are implemented for front-end autocompletion search ({here_frontend_autocomplete_delay}s), and between waypoint info lookups in the backend ({here_backend_lookup_interval}s). These delays do noticably impact performance, and can be removed when running this demo under your own here.com account.</small>"""

    # Calculate button
    calculate = component.Button("calculate", route_panel)
    calculate.label = "Calculate"
    calculate.leftIcon = "fa fa-refresh"
    calculate.block = True
    calculate.theme = "success"
    calculate.setEvent("calculate")
    calculate.addCustomClass("mt-3")
    calculate.disableOnInvalid = True
    calculate.size = "lg"
    calculate.tooltip = "Select truck and 2 to 4 waypoints."

    return route_panel


def create_truck_panel(truck_data) -> component.Panel:
    """Create the truck selection panel."""
    truck_panel = component.Panel("truck_panel")
    truck_panel.title = """Truck Selector"""

    # Store the truck definitions in the app.
    hidden_truck_data = component.Hidden("truckData", truck_panel)
    hidden_truck_data.defaultValue = truck_data

    # Select one truck.
    select_truck = component.Select("selectTruck", truck_panel)
    select_truck.placeholder = "Select a truck"
    select_truck.label = "Select EV Truck"
    select_truck.widget = "choicesjs"
    select_truck.template = (
        f'<img class="route-planner-select-truck-img" src="{TMPL_DISPLAY_DATA_START}item.img_url{TMPL_DISPLAY_DATA_END}"/>'
        f" {TMPL_DISPLAY_DATA_START}item.label{TMPL_DISPLAY_DATA_END}"
    )
    select_truck.dataSrc = "custom"
    select_truck.data = {"custom": "values = data.truckData.vehicles;"}
    select_truck.dataType = "number"
    select_truck.customDefaultValue = "value = data.truckData.vehicles[21];"
    select_truck.setRequired()
    select_truck.labelPosition = "top"

    # Create collapsible panel for truck details
    truck_details_panel = component.Panel("truck_details_panel", truck_panel)
    truck_details_panel.title = """Truck details"""
    truck_details_panel.collapsible = True
    truck_details_panel.collapsed = False
    truck_details_panel.customConditional = (
        "show = data && data.truckData && data.selectTruck.value;"
    )
    # Add large label
    label = component.HtmlElement("truck_label", truck_details_panel)
    label.tag = "h1"
    label.content = f"{TMPL_DISPLAY_DATA_START}data.truckData.vehicles[data.selectTruck.value].label{TMPL_DISPLAY_DATA_END}"
    label.refreshOnChange = True

    # Truck image
    image = component.HtmlElement("truck_image")
    image.tag = "img"
    image.addCustomClass("w-100", "mx-auto", "img-fluid", "pb-3")
    image.setAttrs(
        *zip(
            [
                "src",
                f"{TMPL_DISPLAY_DATA_START}data.selectTruck.value ? data.truckData.vehicles[data.selectTruck.value].img_url : ''{TMPL_DISPLAY_DATA_END}",
            ],
            [
                "title",
                f"{TMPL_DISPLAY_DATA_START}data.selectTruck.value ? data.truckData.vehicles[data.selectTruck.value].img_url: ''{TMPL_DISPLAY_DATA_END}",
            ],
            ["width", "100%"],
        )
    )
    image.refreshOnChange = True

    # Columns for positioninging trick image in middle (and reduce size on large screens)
    img_cols = component.Columns("img_cols", truck_details_panel)
    img_cols.setContent([[], [image], []], [3, 6, 3])

    # Create html component for dynamically displaying manufacturer url in front-end
    url = component.HtmlElement("truck_url", truck_details_panel)
    url.tag = "a"
    url.setAttrs(
        *zip(
            [
                "href",
                f"{TMPL_DISPLAY_DATA_START}data.selectTruck.value ? data.truckData.vehicles[data.selectTruck.value].product_url : ''{TMPL_DISPLAY_DATA_END}",
            ],
            ["target", "_blank"],
        )
    )
    url.content = (
        '<i class="fa fa-globe mr-1"></i>'
        f"{TMPL_DISPLAY_DATA_START}data.selectTruck.value ? data.truckData.vehicles[data.selectTruck.value].product_url : ''{TMPL_DISPLAY_DATA_END}"
    )
    url.refreshOnChange = True

    # Create columns to display truck details
    # Define truck details used for formio template generation.
    # A formio template allows for dynamic display of details dependent on truck selection in front-end.
    # Intended as "advanced example to illustrate custom front-end data display.

    # Speed
    speed_details = {
        "title": "Speed",
        "rows": [
            {
                "label": "Top speed",
                "value": "data.truckData.vehicles[data.selectTruck.value].driveTrain.maxSpeed",
                "unit": "km/h",
            },
            {
                "label": "Euro speed cap",
                "value": "data.truckData.vehicles[data.selectTruck.value].driveTrain.ecoSpeed",
                "unit": "km/h",
            },
        ],
    }
    speed_details_table_template = get_truck_details_table_template(speed_details)

    # Power
    power_details = {
        "title": "Power &amp; Range",
        "rows": [
            {
                "label": "Range",
                "value": "data.truckData.vehicles[data.selectTruck.value].driveTrain.officialRange",
                "unit": "km",
            },
            {
                "label": "Battery capacity",
                "value": "data.truckData.vehicles[data.selectTruck.value].driveTrain.totalBatteryCapacity",
                "unit": "kWh",
            },
        ],
    }
    power_details_table_template = get_truck_details_table_template(power_details)

    # Weight
    weight_details = {
        "title": "Weight",
        "rows": [
            {
                "label": "Gross weight",
                "value": "data.truckData.vehicles[data.selectTruck.value].dimensions.emptyWeight",
                "unit": "kg",
            },
            {
                "label": "Max. payload",
                "value": "data.truckData.vehicles[data.selectTruck.value].dimensions.totalPermittedWeight",
                "unit": "kg",
            },
        ],
    }
    weight_details_table_template = get_truck_details_table_template(weight_details)

    # Charging
    charging_details = {
        "title": "Charging",
        "rows": [
            {
                "label": "AC charging max",
                "value": "data.truckData.vehicles[data.selectTruck.value].driveTrain.acCharging",
                "unit": "kW",
            },
            {
                "label": "DC charging max",
                "value": "data.truckData.vehicles[data.selectTruck.value].driveTrain.dcCharging",
                "unit": "kW",
            },
        ],
    }
    charging_details_table_template = get_truck_details_table_template(charging_details)

    # Components
    table_speed_details = component.HtmlElement("table_speed_details")
    table_speed_details.content = speed_details_table_template
    table_speed_details.refreshOnChange = True

    table_power_details = component.HtmlElement("table_power_details")
    table_power_details.content = power_details_table_template
    table_power_details.refreshOnChange = True

    table_weight_details = component.HtmlElement("table_weight_details")
    table_weight_details.content = weight_details_table_template
    table_weight_details.refreshOnChange = True

    table_charging_details = component.HtmlElement("table_charging_details")
    table_charging_details.content = charging_details_table_template
    table_charging_details.refreshOnChange = True

    # Columns
    cols = component.Columns("truck_details", truck_details_panel)
    left_column, right_column = cols.setContent(
        [
            [table_speed_details, table_weight_details],
            [table_power_details, table_charging_details],
        ],
        [6, 6],
    )
    # Set responsive column breakpoints to xl screen.
    left_column.size = "xl"
    right_column.size = "xl"

    return truck_panel


def get_truck_details_table_template(details) -> str:
    """Generate template syntax for dynamically rendering information in html table"""
    # When a different truck is selected, details tables are rendered directly in frontend.
    # Intended as an example for custom data display without going back to python backend on change.

    # Table start
    table_classes = "table table-bordered table-sm table-responsive w-100 d-table route-planner-truck-property-table"
    table_html = f'<table class="{table_classes}">'

    # Table header and start body
    table_html += (
        f'<thead><tr><td colspan="2"><b>{details["title"]}</b></td></tr></thead><tbody>'
    )

    # Table body rows
    for row in details["rows"]:
        # Formio template code to display value if set, otherwise show dash
        # Uses javascript ternary operator:
        # condition ? exprIfTrue : exprIfFalse
        value_template = f'{TMPL_DISPLAY_DATA_START}{row["value"]} ? {row["value"]} : "-"{TMPL_DISPLAY_DATA_END}'

        # Row with cells containing template code
        table_html += (
            f'<tr><td>{row["label"]}</td><td>{value_template} {row["unit"]}</td></tr>'
        )

    # Table body and table end
    table_html += "</tbody></table>"

    return table_html


def update_plot(plot_obj, locations_data, route):
    """Update the plot with waypoint and route data."""
    lon = []
    lat = []
    auto_zoom = 2

    # Hide selection tools and plotly logo
    plot_obj.config = dict(modeBarButtonsToRemove=["select", "lasso", "logo"])

    # When route is present, extract lon and lat, and calculate a zoom factor
    if route:
        # Prepare route lon, lat info for plotly
        lon, lat = map(list, zip(*route["features"][0]["geometry"]["coordinates"]))
        auto_zoom = calculate_zoom(lon, lat)

    # suboptimal conversion moving from static file based data to here.com data
    if len(locations_data) > 0:
        selected_locations = pd.DataFrame(
            {
                "lat": map(lambda x: x["position"]["lat"], locations_data),
                "lon": map(lambda x: x["position"]["lng"], locations_data),
                "size": map(lambda x: 50, locations_data),
                "title": map(lambda x: x["title"], locations_data),
            }
        )
    else:
        selected_locations = pd.DataFrame(
            {"lat": [], "lon": [], "size": [], "title": []}
        )

    # Draw the waypoints with hover data
    plot_obj.figure = px.scatter_mapbox(
        selected_locations,
        lat="lat",
        lon="lon",
        size="size",
        hover_name=selected_locations.title,
        hover_data={"size": False},
        color_discrete_sequence=["fuchsia"],
        zoom=auto_zoom,
    )

    # Draw the route calculated by openrouteservice.org
    # Hide the coordinates on hover
    plot_obj.figure.add_scattermapbox(
        lon=lon,
        lat=lat,
        hoverinfo="text",
        hovertext="",
        line={"color": "blue", "width": 3},
        mode="lines",
    )

    # Set map style, remove margins and legend
    plot_obj.figure.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
    )


def calculate_zoom(lon: list, lat: list) -> float:
    """Calculate zoom level based on lon lat data."""
    # Zoom calc from: https://github.com/plotly/plotly.js/issues/5296#issuecomment-737435032
    # Notable comment from creator:
    # "I should mention this has only been tested for regional (USA) coordinates, I could see
    # it needing modification when crossing hemispheres/equator"
    zoom_lat = abs(abs(max(lat)) - abs(min(lat)))
    zoom_lon = abs(abs(max(lon)) - abs(min(lon)))
    zoom_factor = max([zoom_lat, zoom_lon])
    if zoom_factor < 0.002:
        zoom_factor = 0.002
    zoom = -1.35 * math.log(float(zoom_factor)) + 7

    return zoom


def get_route(waypoints: list, openrouteservice_api_key: str) -> dict:
    """Do the actual call to openrouteservice.org to get route information."""

    # See: https://openrouteservice.org/dev/#/api-docs
    body = {"coordinates": waypoints}

    headers = {
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
        "Authorization": openrouteservice_api_key,
        "Content-Type": "application/json; charset=utf-8",
    }

    call = requests.post(
        "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
        json=body,
        headers=headers,
    )

    return call


def get_truck_data(image_base_url) -> dict:
    """Read truck info from json file and preprocess for frontend consumption."""
    truck_data_file = path.join(
        path.dirname(path.realpath(__file__)), "resources", "vehicle_data.json"
    )

    with open(truck_data_file) as f:
        truck_data = json.load(f)

    for idx, vehicle in enumerate(truck_data["vehicles"]):
        image_name = (
            re.compile("#pic#([^#]+)").findall(
                vehicle["commercial"]["legacyMarketingField"]
            )[0]
            + ".png"
        )

        vehicle["img_url"] = image_base_url + image_name

        product_url = re.compile("#www#([^#]+)").findall(
            vehicle["commercial"]["legacyMarketingField"]
        )

        if product_url and len(product_url) > 0:
            vehicle["product_url"] = product_url[0]
        else:
            vehicle["product_url"] = ""

        vehicle["label"] = (
            vehicle["commercial"]["manufacturer"]
            + " - "
            + vehicle["commercial"]["model"]
        )

        vehicle["value"] = idx

    return truck_data
