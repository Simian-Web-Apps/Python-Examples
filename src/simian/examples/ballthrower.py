"""Ball Thrower example."""
import logging
import math
import os

from simian.examples.ballthrower_engine import BallThrower
from simian.gui import Form, component, component_properties, utils

# Prepare often used settings.
COLLAPSE_PANEL = {"collapsible": True}
LABEL_LEFT = {"labelPosition": "left-left"}
INLINE = {"customClass": "form-check-inline"}
SHOW_LABEL = {"hideLabel": False}


if __name__ == "__main__":
    # Run as a script
    from simian.entrypoint import assert_simian_gui_imports

    assert_simian_gui_imports()
    from simian.local import Uiformio

    Uiformio("simian.examples.ballthrower", window_title="Ball Thrower example", debug=False)


def gui_event(meta_data: dict, payload: dict) -> dict:
    """Event handling of the application.

    Args:
        meta_data:      Form meta data.
        payload:        Current status of the Form's contents.

    Returns:
        payload:        Updated Form contents.
    """
    try:
        caller = utils.getEventFunction(meta_data, payload)
        payload = caller(meta_data, payload)

    except ImportError as exc:
        # No method with matching name found in the current namespace. May be used to have custom
        # event routing. Here we only log the occurrence.
        logging.debug(exc.msg)

    return payload


def throwing(_meta_data: dict, payload: dict) -> dict:
    """Simulate throwing a ball.

    Get the settings from the payload and multiply with the enabled states to switch off parts of
    the simulation.
    """
    enable_drag, _ = utils.getSubmissionData(payload, key="enableDrag", parent="options")
    enable_wind, _ = utils.getSubmissionData(payload, key="enableWind", parent="options")
    throw_speed, _ = utils.getSubmissionData(payload, key="throwSpeed")
    throw_angle, _ = utils.getSubmissionData(payload, key="throwAngle")
    drag_coeff = utils.getSubmissionData(payload, key="dragCoefficient")[0] * enable_drag
    radius_ball = utils.getSubmissionData(payload, key="ballRadius")[0] * enable_drag
    rho_air = utils.getSubmissionData(payload, key="airDensity")[0] * enable_drag
    gravity = utils.getSubmissionData(payload, key="gravity")[0] * -1  # Point downward.
    mass_ball, _ = utils.getSubmissionData(payload, key="ballMass")  # May not be zero.
    wind_speed = utils.getSubmissionData(payload, key="windSpeed")[0] * enable_drag * enable_wind

    # Convert the speed and angle to the speed components.
    ver_speed = throw_speed * math.sin(throw_angle / 180 * math.pi)
    hor_speed = throw_speed * math.cos(throw_angle / 180 * math.pi)

    _t, x, y, _u, _v = BallThrower.throw_ball(
        u0=hor_speed,
        v0=ver_speed,
        Cd=drag_coeff,
        r=radius_ball,
        rho=rho_air,
        g=gravity,
        m=mass_ball,
        w=wind_speed,
    )

    # Create a Plotly object from the information in the payload.
    plot_obj, _ = utils.getSubmissionData(payload, key="plot")

    # Plot the new newly calculated x and y values, append the legend and put the plotly
    # object in the submission data.
    nr = len(plot_obj.figure.data) + 1
    plot_obj.figure.add_scatter(x=x, y=y, name=f"Attempt {nr}", mode="lines")
    utils.setSubmissionData(payload, key="plot", data=plot_obj)

    # Update the table with the settings used for the throws.
    new_row = [
        nr,
        nr,
        round(hor_speed, 3),
        round(ver_speed, 3),
        wind_speed,
        mass_ball,
        radius_ball,
        drag_coeff,
        gravity,
        rho_air,
    ]

    if nr == 1:
        # First throw. Only put the new row in the table.
        new_table_values = [new_row]
    else:
        # Extra row. Append the row to the DataFrame from the submission data.
        new_table_values, _ = utils.getSubmissionData(payload, key="summary")
        new_table_values.append(dict(zip(new_table_values[0].keys(), new_row)))

    utils.setSubmissionData(payload, key="summary", data=new_table_values)

    # Accept all changes to settings and lower the changes flag.
    payload["pristine"] = True

    return payload


def clearHistory(_meta_data: dict, payload: dict) -> dict:
    """Clears the data from the plot and table."""
    # Clear the data from the plot.
    plot_obj, _ = utils.getSubmissionData(payload, "plot")
    plot_obj.figure.data = []
    utils.setSubmissionData(payload, key="plot", data=plot_obj)

    # Clear the values in the table.
    utils.setSubmissionData(payload, key="summary", data=[])

    payload = utils.addAlert(payload, "History of throws cleared.", "info")

    return payload


def causeError(_meta_data: dict, payload: dict) -> dict:
    """Throws an error so that the user can see the error handling in action."""
    raise RuntimeError("Error thrown for testing the error handling mechanism.")


def gui_init(*_args) -> dict:
    """Initializes the form.

    Initialization of the form and the components therein.

    Returns:
        payload:    Form definition.
    """
    # Create a form object as the base of the application.
    form_obj = Form()

    # Create tabs in the form.
    tabs = component.Tabs(key="tabs", parent=form_obj)
    tab_inputs, tab_settings = tabs.setContent(labels=["Inputs", "Used settings"])

    # Create a Columns object and fill it with two empty columns.
    col = component.Columns(key="inputColumns", parent=tab_inputs)
    left_column, right_column = col.setContent(components=[], widths=[6, 6])

    # Options Panel
    wind_options = {"logic": _wind_options(), **INLINE}

    # Turn off black formatter for readability of build tables.
    utils.addComponentsFromTable(
        parent=left_column,
        build_table=[
            # key           class           level   options         default     label           tooltip
            ["options",     "Container",    1,      SHOW_LABEL,     None,       "Options:",     None],
            ["enableDrag",  "Checkbox",     2,      INLINE,         False,      "Enable Drag",  "Enable the simulation of the effect of drag on the thrown ball."],
            ["enableWind",  "Checkbox",     2,      wind_options,   False,      "Enable Wind",  "Enable the simulation of the effect of wind on the thrown ball. Requires drag to be enabled."]  # fmt: skip
        ],
    )

    # Add Throw speed and angle controls.
    add_throw_speed_controls(left_column)

    # Add the Throw, Ball, Constants and Wind panels to the left column.
    _add_options_panels(left_column)

    # Fill the right column.
    fill_right_column(right_column)

    # Fill the Settings tab.
    _fill_settings_tab(tab_settings)

    # Define the logo.
    image_file = os.path.join(os.path.dirname(__file__), "logo.png")
    logo = utils.encodeImage(image_file)

    # Put the form in the outputs.
    payload = {
        "form": form_obj,
        "navbar": {
            "logo": logo,
            "title": "Ball Thrower",
            "subtitle": "<small>Simian Demo</small>",
        },
        "showChanged": True,  # Flag changes to the settings in the UI.
    }

    return payload


def add_throw_speed_controls(parent) -> dict:
    """Create and add Throw speed and angle controls."""
    # Allow speed values between 0 and 20 m/s.

    speed_options = {
        "validate": {
            "min": 0,
            "max": 20 * math.sqrt(2),
            "required": True,
        },
        **LABEL_LEFT,
    }

    angle_options = {
        "validate": {
            "min": 0,
            "max": 90,
            "required": True,
        },
        **LABEL_LEFT,
    }

    # Throw Panel
    return utils.addComponentsFromTable(
        parent=parent,
        build_table=[
            # key               class       level   options         default label                       tooltip
            ["throwPanel",      "Panel",    1,      COLLAPSE_PANEL, None,   "Throw settings",           None],
            ["throwSpeed",      "Number",   2,      speed_options,  10,     "Throw speed [m/s]:",       "Speed with which the ball is thrown."],
            ["throwAngle",      "Number",   2,      angle_options,  45,     "Throw angle [degrees]:",   "Angle at which the ball is thrown."]  # fmt: skip
        ],
    )


def _add_options_panels(left_column):
    # Ball properties
    # Hide ball panel when drag is not enabled.
    show_drag_enabled = {"customConditional": "show=data.options.enableDrag"}
    ball_panel_opts = {
        **show_drag_enabled,
        **COLLAPSE_PANEL,
    }

    # Ball mass number, allow values larger than 0.
    ball_mass_opts = {
        "validate": {
            "min": 0.000001,
            "required": True,
        },
        **LABEL_LEFT,
    }

    # Ball radius number, allow values larger than 0.
    ball_radius_opts = {
        "validate": {
            "min": 0,
            "required": True,
        },
        **LABEL_LEFT,
    }

    # Drag coefficient number, allow values between 0 and 10.
    drag_coeff_opts = {
        "validate": {
            "min": 0,
            "max": 10,
            "required": True,
        },
        **LABEL_LEFT,
    }

    utils.addComponentsFromTable(
        parent=left_column,
        build_table=[
            # key               class       level   options             default label                       tooltip
            ["ballPanel",       "Panel",    1,      ball_panel_opts,    None,   "Ball settings",            None],
            ["ballMass",        "Number",   2,      ball_mass_opts,     0.05,   "Mass [kg]:",               "Mass of the ball."],
            ["ballRadius",      "Number",   2,      ball_radius_opts,   0.1,    "Radius [m]:",              "Radius of the ball."],
            ["dragCoefficient", "Number",   2,      drag_coeff_opts,    0.4,    "Drag coefficient [-]:",    "Drag coefficient of the ball."]  # fmt: skip
        ],
    )

    # Constants Panel
    # Allow gravity values between 0.1 and 20 m/s^2.
    gravity_opts = {
        "validate": {
            "min": 0.1,
            "max": 20,
            "required": True,
        },
        **LABEL_LEFT,
    }

    # Air density number, allow values between 0 and 10 kg/m^3.
    air_dens_opts = {
        **show_drag_enabled,
        "validate": {
            "min": 0,
            "max": 10,
            "required": True,
        },
        **LABEL_LEFT,
    }

    utils.addComponentsFromTable(
        parent=left_column,
        build_table=[
            # key               class       level   options             default label                               tooltip
            ["constantsPanel",  "Panel",    1,      COLLAPSE_PANEL,     None,   "Constants",                        None],
            ["gravity",         "Number",   2,      gravity_opts,       9.81,   "Gravity [m/s<sup>2</sup>]:",       "Gravitational accelleration acting on the ball."],
            ["airDensity",      "Number",   2,      air_dens_opts,      1.29,   "Air density [kg/m<sup>3</sup>]:",  "Density of the air through which the ball moves."]  # fmt: skip
        ],
    )

    # Wind Panel
    # Hide wind panel when wind is not enabled.
    wind_panel_options = {
        "conditional": {
            "when": "enableWind",
            "eq": False,
        },
        **COLLAPSE_PANEL,
    }

    # Allow wind speed number values between -10 and 10 m/s.
    wind_options = {
        "validate": {
            "min": -10,
            "max": 10,
            "required": True,
        },
        **LABEL_LEFT,
    }

    utils.addComponentsFromTable(
        parent=left_column,
        build_table=[
            # key           class       level   options             default label                  tooltip
            ["windPanel",   "Panel",    1,      wind_panel_options, None,   "Wind settings",       None],
            ["windSpeed",   "Number",   2,      wind_options,       -1,     "Wind speed [m/s]:",   "Wind speed. Positive values correspond with tailwind. Negative values correspond with headwind."]  # fmt: skip
        ],
    )


def fill_right_column(right_column) -> None:
    """Fill right column of the app."""
    # Actions Panel
    throw_options = {"disableOnInvalid": True, **INLINE}
    error_options = {"theme": "danger", **INLINE}

    buttons_dict = utils.addComponentsFromTable(
        parent=right_column,
        build_table=[
            # key           class           level   options         label               tooltip
            ["ButtonPanel", "Container",    1,      SHOW_LABEL,     "Actions:",         None],
            ["throwButton", "Button",       2,      throw_options,  "Throw",            "Click to simulate a throw with the chosen settings."],
            ["clearButton", "Button",       2,      INLINE,         "Clear results",    "Click to remove all of the current results."],
            ["errorButton", "Button",       2,      error_options,  "Cause error",      "Click to cause an error and see the error handling in action."]  # fmt: skip
        ],
        column_names=["key", "class", "level", "options", "label", "tooltip"],
    )

    # Add the events to the buttons.
    buttons_dict["throwButton"].setEvent(event_name="throwing")
    buttons_dict["clearButton"].setEvent(event_name="clearHistory")
    buttons_dict["errorButton"].setEvent(event_name="causeError")

    # Plot
    # Create a plot window to plot the ball trajectories in.
    my_plot = component.Plotly(key="plot", parent=right_column)
    my_plot.defaultValue["data"] = []
    my_plot.defaultValue["layout"] = {
        "title": {"text": "Balls thrown"},
        "xaxis": {"title": "Distance [m]"},
        "yaxis": {"title": "Height [m]"},
        "margin": {"t": 40, "b": 30, "l": 50},
    }
    my_plot.defaultValue["config"] = {"displaylogo": False}


def _fill_settings_tab(tab_settings):
    """Fill Settings tab."""
    # Create a table to store the throw settings in.
    table_out = component.DataTables(key="summary", parent=tab_settings)
    table_out.label = "Used settings per throw"
    table_out.setFeatures(searching=False, ordering=False, paging=False)
    table_out.setColumns(
        *[
            list(x)
            for x in zip(
                ["Id", "id"],
                ["Attempt", "attempt"],
                ["Horizontal speed", "hor_speed"],
                ["Vertical speed", "ver_speed"],
                ["Wind speed", "wind_speed"],
                ["Ball mass", "ball_mass"],
                ["Radius", "radius"],
                ["Drag Coeff.", "drag"],
                ["Gravity", "gravity"],
                ["Air density", "air_density"],
            )
        ],
        visible=[False] + [True] * 9,
    )


def _wind_options() -> list:
    """Define drag enabled/disabled triggers."""
    # Disable the Wind checkbox when the Drag checkbox is unticked.
    wind_disable = component_properties.create_disable_logic(
        trigger_type="simple", trigger_value=["enableDrag", False]
    )

    # Ensure the Wind checkbox is unticked when Drag is unticked.
    wind_disable.actions.append(
        {
            "type": "value",
            "value": "value = false",
        }
    )
    return wind_disable
