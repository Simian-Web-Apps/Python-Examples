"""Simian-GUI plots examples application.

The plots shown in this application are created with the Python Plotly library. For more information
about Plotly refer to: https://plotly.com/python/.
"""
import inspect
import os
import textwrap

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from simian.gui import Form, component, utils

# Prepare some pandas DataFrames with demo data.
GAP_MINDER = px.data.gapminder()
DATA_TIPS = px.data.tips()
STOCKS = px.data.stocks()

# Initialize defaults.
PLOTS_DICT = {}
BASE_LABEL = "Select a plot to show."


if __name__ == "__main__":
    # Show the application in a Simian-Local window when the module is run as a script.
    from simian.entrypoint import assert_simian_gui_imports

    assert_simian_gui_imports()
    from simian.local import Uiformio

    Uiformio("simian.examples.plottypes", window_title="Plot types examples", debug=False)


def register_type(name):
    """Decorator initialization function with registration name input."""

    def dec(func):
        """Decorator function with the to decorate function as input."""

        def wrapped_func(payload) -> dict:
            """Wrapper around plot function."""
            # Create a new Plotly object to get a clean starting point.
            plot_obj = utils.Plotly()
            func(plot_obj)

            # Ensure the margins remain small.
            plot_obj.figure.layout.margin.t = 40
            plot_obj.figure.layout.margin.b = 30
            plot_obj.figure.layout.margin.l = 50

            # Put the new plot contents in the payload.
            utils.setSubmissionData(payload, "plot", plot_obj)

            # Use the decorated function's docstring as description.
            doc_string = textwrap.dedent("    " + func.__doc__)
            utils.setSubmissionData(payload, key="description", data=doc_string.strip())

            # Show the code of the decorated function in the app.
            utils.setSubmissionData(
                payload,
                key="code_block",
                data=f"<pre><code>{inspect.getsource(func)}</code></pre>",
            )

            return payload

        # Register the plot type in the dictionary.
        PLOTS_DICT.update({name: wrapped_func})

        return wrapped_func

    return dec


def gui_event(_meta_data: dict, payload: dict) -> dict:
    """Event handling of the application.

    Args:
        meta_data:      Form meta data.
        payload:        Current status of the Form's contents.

    Returns:
        payload:        Updated Form contents.
    """
    # No need to check where the event is coming from; only the plot_selection component can trigger
    # events. Get the selected plot.
    plot_selection, _ = utils.getSubmissionData(payload, key="plot_selection")

    if plot_selection in PLOTS_DICT:
        # Switch to the function that was registered for the plot type.
        plot_func = PLOTS_DICT[plot_selection]
        plot_func(payload=payload)

    else:
        # No selection. Clear the figure.
        plot_obj, _ = utils.getSubmissionData(payload, "plot")
        plot_obj.figure.data = []
        plot_obj.figure.layout.title = BASE_LABEL
        plot_obj.figure.layout.xaxis.title = {}
        plot_obj.figure.layout.yaxis.title = {}
        utils.setSubmissionData(payload, key="plot", data=plot_obj)

        # Replace the description and code block with the default text.
        utils.setSubmissionData(payload, key="description", data=BASE_LABEL)
        utils.setSubmissionData(payload, key="code_block", data=BASE_LABEL)

    return payload


def gui_init(*_args) -> dict:
    """Initializes the form.

    Initialization of the form and the components therein.

    Returns:
        payload:    Form definition.
    """
    # Create a form object as the base of the application.
    form_obj = Form()

    plot_defaults = {
        "data": [],
        "layout": {
            "title": {"text": BASE_LABEL},
            "margin": {"t": 40, "b": 30, "l": 50},
        },
        "config": {"displaylogo": False},
    }
    disable = {"disabled": True}
    col_opts = {"width": 6}

    # Turn off black formatter for readability of build tables.
    base_controls = utils.addComponentsFromTable(
        parent=form_obj,
        build_table=[
            # key               class       lvl options         default
            ["columns",         "Columns",  1,  None,           None],
            ["left_column",     "column",   2,  col_opts,       None],
            ["right_column",    "column",   2,  col_opts,       None],
            ["plot",            "Plotly",   3,  None,           plot_defaults],  # fmt: skip
        ],
        column_names=["key", "class", "level", "options", "defaultValue"],
    )

    controls_dict = utils.addComponentsFromTable(
        parent=base_controls["left_column"],
        build_table=[
            # key               class       lvl options         default         label
            ["plot_selection",  "Select",   1,  None,           None,           "Select a plot type"],
            ["description",     "TextArea", 1,  disable,        BASE_LABEL,     None],
            ["panel",           "Panel",    1,  None,           None,           "Source code"],
            ["code_block",      "Html",     2,  disable,        BASE_LABEL,     None],  # fmt: skip
        ],
        column_names=["key", "class", "level", "options", "defaultValue", "label"],
    )

    # Put the plot types in the select component.
    controls_dict["plot_selection"].setValues(PLOTS_DICT.keys(), PLOTS_DICT.keys())
    controls_dict["plot_selection"].properties = {"triggerHappy": True}

    # Define the logo.
    image_file = os.path.join(os.path.dirname(__file__), "logo.png")
    logo = utils.encodeImage(image_file)

    # Put the form in the outputs.
    payload = {
        "form": form_obj,
        "navbar": {
            "logo": logo,
            "title": "Plot examples",
            "subtitle": "<small>Simian Demo</small>",
        },
    }

    return payload


@register_type("Bar")
def show_bar(plot_obj: component.Component) -> None:
    """Bar plot showing GAP minder data with Plotly visualization."""
    plot_obj.figure = px.bar(
        GAP_MINDER.query("year==2007"),
        x="continent",
        y="pop",
        color="country",
        title="Populations in 2007",
        text="country",
    )


@register_type("Box plot")
def show_box_plot(plot_obj: component.Component) -> None:
    """Box plot showing restaurant bills with Plotly visualization."""
    plot_obj.figure = px.box(
        DATA_TIPS,
        x="day",
        y="total_bill",
        color="time",
        notched=True,
        title="Box plot of total bill",
        hover_data=["day"],
    )


@register_type("CDF")
def show_ecdf(plot_obj: component.Component) -> None:
    """Empirical Cumulative Distribution Function of restaurant bills Plotly visualization."""
    plot_obj.figure = px.ecdf(
        DATA_TIPS,
        x="total_bill",
        title="Restaurant bills",
        marginal="histogram",
        color="time",
    )


@register_type("Contour")
def show_contour(plot_obj: component.Component) -> None:
    """Contour plot with Plotly visualization."""
    plot_obj.figure = go.Figure(
        data=go.Contour(
            z=[
                [2, 4, 7, 12, 13, 14, 15, 16],
                [3, 1, 6, 11, 12, 13, 16, 17],
                [4, 2, 7, 7, 11, 14, 17, 18],
                [5, 3, 8, 8, 13, 15, 18, 19],
                [7, 4, 10, 9, 16, 18, 20, 19],
                [9, 10, 5, 27, 23, 21, 21, 21],
                [11, 14, 17, 26, 25, 24, 23, 22],
            ],
            contours={
                "coloring": "heatmap",
                "showlabels": True,  # show labels on contours
                "labelfont": {  # label font properties
                    "size": 12,
                    "color": "white",
                },
            },
        ),
        layout={"title": {"text": "Contour example"}},
    )


@register_type("Draw shapes")
def show_drawing(plot_obj: component.Component) -> None:
    """Line plot showing stock market data with Plotly visualization.

    Shapes can be drawn on and erased from the plot with the options in the toolbar.
    """
    plot_obj.figure = px.line(
        STOCKS,
        x="date",
        y=STOCKS.columns,
        hover_data={"date": "|%B %d, %Y"},
        title="Stock market data",
    )
    plot_obj.figure.update_layout(
        title_text="Draw shapes example",
        dragmode="drawopenpath",
        newshape_line_color="cyan",
    )
    plot_obj.config.update(
        {
            "modeBarButtonsToAdd": [
                "drawline",
                "drawopenpath",
                "drawclosedpath",
                "drawcircle",
                "drawrect",
                "eraseshape",
            ]
        }
    )


@register_type("Heat map")
def show_heatmap(plot_obj: component.Component) -> None:
    """Heat map overlain with data points showing restaurant bills with Plotly visualization.

    The histograms on the axes are easy to add options.
    """
    plot_obj.figure = px.density_heatmap(
        DATA_TIPS,
        x="total_bill",
        y="tip",
        marginal_x="histogram",
        marginal_y="histogram",
    )

    # Add markers to measurement locations.
    plot_obj.figure.add_trace(
        go.Scatter(
            x=DATA_TIPS["total_bill"],
            y=DATA_TIPS["tip"],
            mode="markers",
            showlegend=False,
        )
    )


@register_type("Line")
def show_line(plot_obj: component.Component) -> None:
    """Line plot showing stock market data with Plotly visualization.

    Note that in the bottom subplot the date range of the main plot can be changed.
    """
    plot_obj.figure = px.line(
        STOCKS,
        x="date",
        y=STOCKS.columns,
        hover_data={"date": "|%B %d, %Y"},
        title="Stock market data",
    )

    plot_obj.figure.update_xaxes(
        dtick="M1",
        tickformat="%b\n%Y",
        ticklabelmode="period",
        rangeslider_visible=True,
    )


@register_type("Map")
def show_map(plot_obj: component.Component) -> None:
    """Map showing GAP minder data with Plotly visualization."""
    plot_obj.figure = px.scatter_geo(
        GAP_MINDER.query("year==2007"),
        locations="iso_alpha",
        color="gdpPercap",
        hover_name="country",
        size="pop",
        size_max=60,
        projection="natural earth",
        title="GDP and population in 2007",
    )


@register_type("Mesh")
def show_mesh(plot_obj: component.Component) -> None:
    """Mesh grid showing random data with Plotly visualization."""
    nr_points = 25
    plot_obj.figure = go.Figure(
        data=[
            go.Mesh3d(
                x=(30 * np.random.randn(nr_points)),
                y=(25 * np.random.randn(nr_points)),
                z=(30 * np.random.randn(nr_points)),
                opacity=0.5,
            )
        ]
    )

    grid_defaults = {
        "gridcolor": "white",
        "showbackground": True,
        "zerolinecolor": "white",
    }

    # xaxis.backgroundcolor is used to set background color
    plot_obj.figure.update_layout(
        scene={
            "xaxis": {"backgroundcolor": "rgb(200, 200, 230)", **grid_defaults},
            "yaxis": {"backgroundcolor": "rgb(230, 200, 230)", **grid_defaults},
            "zaxis": {"backgroundcolor": "rgb(230, 230, 200)", **grid_defaults},
        },
        margin={"r": 10, "l": 10, "b": 10, "t": 10},
    )


@register_type("Pie")
def show_pie(plot_obj: component.Component) -> None:
    """Pie chart showing GAP minder data over the years with Plotly visualization.

    The Plotly express `facet` options allow for easier subplot generation.
    """
    plot_obj.figure = px.pie(
        GAP_MINDER,
        values="pop",
        names="country",
        facet_col="year",
        facet_col_wrap=4,
    )
    plot_obj.figure.update_traces(textposition="inside")
    plot_obj.figure.update_layout(
        uniformtext_minsize=12,
        uniformtext_mode="hide",
    )


@register_type("Scatter")
def show_scatter(plot_obj: component.Component) -> None:
    """Scatter plot showing GAP minder data with Plotly visualization."""
    plot_obj.figure = px.scatter(
        GAP_MINDER.query("year==2007"),
        x="gdpPercap",
        log_x=True,
        y="lifeExp",
        symbol="year",
        size="pop",
        size_max=60,
        color="continent",
        hover_name="country",
        title="GDP and life expectancy in 2007",
    )


@register_type("Scatter 3D")
def show_scatter3d(plot_obj: component.Component) -> None:
    """3D Scatter plot showing GAP minder data with Plotly visualization.

    Pan, zoom and rotate the plot to inspect its contents.
    """
    # https://plotly.com/python/line-and-scatter/
    plot_obj.figure = px.scatter_3d(
        GAP_MINDER,
        x="year",
        y="gdpPercap",
        log_y=True,
        z="lifeExp",
        size="pop",
        size_max=60,
        color="continent",
        hover_name="country",
        title="GDP and life expectancy",
    )
    plot_obj.figure.update_layout(scene_aspectmode="auto")
