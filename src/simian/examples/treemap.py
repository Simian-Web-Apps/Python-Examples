"""Treemap example.

Uses the Plotly component to create a treemap https://plotly.com/javascript/reference/treemap/.
"""

import numpy as np
import pandas as pd
import plotly.express as px
from simian.gui import Form, component, utils

if __name__ == "__main__":
    from simian.local import Uiformio

    Uiformio("simian.examples.treemap", window_title="Treemap Example")


# Load the gapminder dataset.
GAPMINDER_DATA = px.data.gapminder()


def gui_init(_meta_data: dict) -> dict:
    """Initializes the form.

    Args:
        _meta_data (dict): Meta data.

    Returns:
        dict: Payload with form definition.
    """

    # Register component initializers.
    Form.componentInitializer(
        treemap=_init_treemap,
        year=_init_year,
        treemapPreloaded=_init_treemap_preloaded,
        preloadedData=_init_preloaded_data,
    )

    # Create the form and load the json builder into it.
    form = Form(from_file=__file__)

    # Add the form to the payload and set the title on the navbar.
    return {
        "form": form,
        "navbar": {"title": "World population and life expectancy"},
    }


def _init_treemap(comp: component.Plotly):
    # Initialize the treemap with data from the year 2007.
    comp.figure = _select_year(2007)


def _init_year(comp: component.Slider):
    # Make the slider emit events one second after each change. Only the last value is used.
    comp.addCustomProperty("triggerHappy", "YearSelected")
    comp.addCustomProperty("debounceTime", 1000)


def _init_treemap_preloaded(comp: component.Plotly):
    # Set the calculateValue to call the JavaScript function that selects the data for the year.
    comp.setCalculateValue("value = fillTreemap(data.preloadedData, data.yearPreloaded);")
    comp.figure = _select_year(2007)


def _init_preloaded_data(comp: component.Hidden):
    # Aggregate data for continent and world.
    cont_data = _aggregate_gapminder(["continent", "year"])
    world_data = _aggregate_gapminder(["year"])
    full_data = pd.concat([GAPMINDER_DATA, cont_data, world_data])
    full_data["world"] = "world"

    # Get the full identifier of the row: "world/<continent>/<country>". Parts that do not exist are
    # not added.
    row_ids = full_data[["world", "continent", "country"]].apply(
        lambda r: r.str.cat(sep="/"), axis=1
    )

    # Split the row identifiers in their own name and the parent.
    parents, _, own_name = zip(*(id.rpartition("/") for id in row_ids))

    # Set the default value of the hidden component.
    comp.defaultValue = {
        "countries": own_name,
        "parents": parents,
        "ids": list(row_ids),
        "lifeExp": list(full_data["lifeExp"]),
        "pop": list(full_data["pop"]),
        "years": list(full_data["year"]),
    }


def gui_event(meta_data: dict, payload: dict) -> dict:
    """Handle events of the application.

    Args:
        meta_data (dict): Meta data.
        payload (dict): Payload including submission data from the user interface.

    Returns:
        dict: Updated payload data.
    """

    # Register event handlers.
    Form.eventHandler(YearSelected=_update_year)

    # Handle the event using the event data in the payload.
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def _update_year(_meta_data: dict, payload: dict) -> dict:
    # Get the year and treemap.
    year, _ = utils.getSubmissionData(payload, "year")
    treemap, _ = utils.getSubmissionData(payload, "treemap")

    # Update the layout and plot data with the data of the selected year.
    treemap.figure = _select_year(year)

    # Set the treemap value.
    utils.setSubmissionData(payload, "treemap", treemap)

    return payload


def _select_year(year: int):
    # Get the data for the year.
    yearData = GAPMINDER_DATA.query(f"year == {year}")

    # Update the treemap data and layout.
    fig = px.treemap(
        yearData,
        path=[px.Constant("world"), "continent", "country"],
        values="pop",
        color="lifeExp",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=np.average(yearData["lifeExp"], weights=yearData["pop"]),
    )

    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

    return fig


def _aggregate_gapminder(grouping: str) -> pd.DataFrame:
    """Aggregate population and life expectancy data."""
    grouped_gaps = GAPMINDER_DATA.groupby(grouping)

    # Total population of a group is the sum of its parts.
    pop = grouped_gaps["pop"].sum()

    # Total life expectancy of a group is the mean weighted with the population of its parts.
    life_exp = grouped_gaps.apply(lambda x: np.average(x["lifeExp"], weights=x["pop"]))
    life_exp.name = "lifeExp"

    # Join the tables.
    return pd.concat([pop, life_exp], axis=1).reset_index()
