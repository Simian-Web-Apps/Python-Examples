"""App containing all component types."""
from pathlib import Path

import numpy as np
from simian.gui import Form, component, utils

COMPONENTS_LEVEL = 1


if __name__ == "__main__":
    # Run as a script
    from simian.entrypoint import assert_simian_gui_imports

    assert_simian_gui_imports()
    from simian.local import Uiformio

    Uiformio(
        "simian.examples.all_components", size=[1280, 720], window_title="All Components Example"
    )


def gui_init(_):
    """Initialize form with components."""
    # Initialize the form.
    form = Form()

    # Generate all component types.
    build_list = _generate_components_with_type(COMPONENTS_LEVEL)
    col_opts = {"width": 6}

    # Build the form.
    created_components = utils.addComponentsFromTable(
        parent=form,
        build_table=[
            # key               class       lvl options     default label                       tooltip
            ["columns",         "Columns",  1,  None,       None,   None,                       None],
            ["left_column",     "column",   2,  col_opts,   None,   None,                       None],
            ["selector",        "Select",   3,  None,       None,   "Select component type",    "Choose the component type that you want to see."],
            ["right_column",    "column",   2,  col_opts,   None,   None,                       None],  # fmt: skip
        ],
    )
    # Put all generated root components in the options list of the component selector.
    created_components["selector"].setValues(
        [c[5] for c in build_list if c[2] == COMPONENTS_LEVEL and c[5] is not None],
        [c[0] for c in build_list if c[2] == COMPONENTS_LEVEL and c[5] is not None],
    )

    # Add the components to the right column.
    utils.addComponentsFromTable(created_components["right_column"], build_list)

    # Define the logo.
    image_file = str(Path(__file__).parent / "logo.png")
    logo = utils.encodeImage(image_file)

    return {
        "form": form,
        "navbar": {
            "title": "All Components Example",
            "subtitle": "<small>Simian Demo</small>",
            "logo": logo,
        },
    }


def gui_event(_, payload):
    """Handle events."""
    return payload


def _generate_components_with_type(base_level: int) -> list:
    """Create a list with instances of all subclasses of Component."""
    classes = component.Component.__subclasses__()
    classes.extend(component.Html.__subclasses__())
    class_names = [cls.__name__ for cls in classes]

    # We do not support the Address component and it is undocumented. See issue #216.
    address_idx = class_names.index("Address")
    class_names.pop(address_idx)
    classes.pop(address_idx)

    # Do not show the Builder as a component.
    builder_idx = class_names.index("Builder")
    class_names.pop(builder_idx)
    classes.pop(builder_idx)

    sort_order = np.argsort(class_names)

    # Initialize the buildTable.
    build_array = []

    # Add a row for each class.
    for class_idx in sort_order:
        if class_names[class_idx] in ["Form", "Container"]:
            # Exclude Form - it is not relevant for this example.
            continue

        constructor = classes[class_idx]
        label = class_names[class_idx]
        tester = constructor(label + str(base_level))
        default_value = _get_default_value(tester.key)
        opts = _get_options(tester.key)

        if base_level == COMPONENTS_LEVEL:
            # Top-level: add conditional to show the component.
            cond_opts = {"conditional": {"show": True, "when": "selector", "eq": tester.key}}

            if opts:
                opts.update(cond_opts)
            else:
                opts = cond_opts

            doc = _get_doc(label)
            doc_link = f'<p><small><a href="{doc}" target="_blank"><i class="fa fa-book"></i> Documentation</a></small></p>'
            build_array.append(
                [tester.key + "Doc", "Html", base_level, cond_opts, doc_link, None, None]
            )

        build_array.append([tester.key, tester.type, base_level, opts, default_value, label, None])

        if base_level == COMPONENTS_LEVEL:
            # Top-level: add components to capable classes.
            if tester.hasComponents():
                # Add components: some special cases.
                if tester.type == "address":
                    # Not possible to add components, even though it has a components field.
                    pass
                elif tester.type == "tabs":
                    # Only tabs can be added - but they are stored in the components field...
                    build_array.extend(
                        [
                            [tester.key + "tab1",       "tab",          base_level + 1, None, None, "Tab 1",        None],
                            [tester.key + "tab1dummy",  "textfield",    base_level + 2, None, None, "Text Field",   None],
                        ]
                    )  # fmt: skip
                    build_array.extend(
                        [
                            [tester.key + "tab2",       "tab",          base_level + 1, None, None, "Tab 2",        None],
                            [tester.key + "tab2dummy",  "textfield",    base_level + 2, None, None, "Text Field",   None],
                        ]
                    )  # fmt: skip
                else:
                    # Panel, Container, etc.
                    build_array.extend(_add_subcomponents(tester.key))
            elif tester.type == "columns":
                # Columns are not stored in the components field.
                build_array.extend(
                    [
                        [tester.key + "col1",       "column",       base_level + 1, {"width": 9},   None, None,         None],
                        [tester.key + "col1dummy",  "textfield",    base_level + 2, None,           None, "Text Field", None],
                    ]
                )  # fmt: skip
                build_array.extend(
                    [
                        [tester.key + "col2",       "column",       base_level + 1, {"width": 3},   None, None,         None],
                        [tester.key + "col2dummy",  "textfield",    base_level + 2, None,           None, "Text Field", None],
                    ]
                )  # fmt: skip
            elif tester.type == "table":
                for r in range(2):
                    build_array.append(
                        [f"{tester.key}row{r}", "tablerow", base_level + 1, None, None, None, None]
                    )
                    for c in range(2):
                        build_array.extend(
                            [
                                [f"{tester.key}cell{r}{c}", "tablecell", base_level + 2, None, None, None, None],
                                [f"{tester.key}comp{r}{c}", "textfield", base_level + 3, None, None, None, None],
                            ]
                        )  # fmt: skip

    return build_array


def _get_default_value(component_key: str):
    return _get_default_values().get(component_key)


def _get_default_values():
    return {
        "Address1": {
            "place_id": 26591519,
            "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
            "osm_type": "node",
            "osm_id": 2735607631,
            "boundingbox": ["51.573239", "51.573339", "4.8052079", "4.8053079"],
            "lat": "51.573289",
            "lon": "4.8052579",
            "display_name": "71, Groot Ypelaardreef, Breda, North Brabant, Netherlands, 4834 HC, Netherlands",
            "class": "place",
            "type": "house",
            "importance": 0.4200999999999999,
            "address": {
                "house_number": "71",
                "road": "Groot Ypelaardreef",
                "city": "Breda",
                "municipality": "Breda",
                "state": "North Brabant",
                "ISO3166-2-lvl4": "NL-NB",
                "country": "Netherlands",
                "postcode": "4834 HC",
                "country_code": "nl",
            },
        },
        "Checkbox1": True,
        "Currency1": 1.23,
        "DataMap1": {"background": "#cccccc", "font-size": "1.25rem"},
        "DataTables1": {
            "data": [
                {"id": "Bob", "age": 49, "present": "Yes"},
                {"id": "Sarah", "age": 47, "present": "No"},
            ],
            "dtOptions": {
                "columns": [
                    {"data": "id", "title": "Name"},
                    {"data": "age", "title": "Age"},
                    {"data": "present", "title": "Present"},
                ]
            },
            "dtFunctions": {"columns": []},
            "editorMode": {},
            "editorOptions": {},
            "tableId": "this-table-is-unique",
        },
        "DateTime1": "2023-04-26 14:52:00Z",
        "Day1": "04/04/2023",
        "EditGrid1": [{"eg1": "Info", "eg2": "info@monkeyproofsolutions.nl"}],
        "Email1": "info@simiansuite.com",
        "Hidden1": '<h3 class="display-3">Content (static HTML)</h3>',
        "Html1": '<h3 class="display-3">Custom HTML</h3>',
        "HtmlTable1": """<table class="table">
    <thead>
        <tr><th scope="col">Name</th><th scope="col">Age</th><th scope="col">Present</th></tr>
    </thead>
    <tbody>
        <tr><td>Bob</td><td>49</td><td>Yes</td></tr>
        <tr><td>Sarah</td><td>47</td><td>No</td></tr>
    </tbody>
</table>""",
        "Number1": 12345,
        "Password1": "y0uCaNn0tSe3m3",
        "Phonenumber1": "(123) 456-7890",
        "Plotly1": _plotly_default_value(),
        "ResultFile1": _resultfile_default_value(),
        "Tags1": ["bug", "feature", "enhancement"],
        "TextArea1": """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.""",
        "TextField1": "Lorem ipsum",
        "Time1": "15:13",
    }


def _get_doc(label: str):
    return f"https://doc.simiansuite.com/simian-gui/v2.0/initialization/{label.lower()}.html"


def _get_options(component_key: str):
    return _get_default_options().get(component_key)


def _get_default_options():
    return {
        "Address1": {
            "provider": "nominatim",
            "providerOptions": {"params": {}},
        },
        "Content1": {"html": '<span class="lead">Static HTML content</span>'},
        "DataMap1": {
            "valueComponent": {
                "type": "textfield",
                "key": "value",
                "label": "Value",
                "input": True,
                "hideLabel": True,
                "tableView": True,
            },
        },
        "FieldSet1": {"legend": "FieldSet"},
        "HtmlElement1": {"tag": "h3", "content": "Static HTML element"},
        "Panel1": {"collapsible": True},
        "PhoneNumber1": {
            "applyMaskOn": "change",
        },
        "Radio1": {
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
                {"label": "C", "value": "c"},
            ]
        },
        "Select1": {
            "dataSrc": "values",
            "data": {
                "values": [
                    {"label": "A", "value": "a"},
                    {"label": "B", "value": "b"},
                    {"label": "C", "value": "c"},
                ]
            },
        },
        "Selectboxes1": {
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
                {"label": "C", "value": "c"},
            ]
        },
        "Survey1": {
            "questions": [
                {
                    "label": "How would you rate this question on a scale of 1 to 5?",
                    "value": "score",
                },
                {"label": "And this one?", "value": "thisOne"},
            ],
            "values": [
                {"label": "1", "value": "a"},
                {"label": "2", "value": "b"},
                {"label": "3", "value": "c"},
                {"label": "4", "value": "d"},
                {"label": "5", "value": "e"},
            ],
        },
    }


def _add_subcomponents(component_key):
    return _get_default_comps().get(component_key, [])


def _get_default_comps():
    return {
        "DataGrid1": [
            ["dg1", "textfield", 2, None, None, "First", None],
            ["dg2", "textfield", 2, None, None, "Second", None],
        ],
        "EditGrid1": [
            ["eg1", "textfield", 2, None, None, "Name", None],
            ["eg2", "email", 2, None, None, "Email", None],
        ],
        "FieldSet1": [
            ["fs1", "textfield", 2, None, None, "Name", None],
            ["fs2", "email", 2, None, None, "Email", None],
        ],
        "Panel1": [
            ["pan1", "textfield", 2, None, None, "Name", None],
            ["pan2", "email", 2, None, None, "Email", None],
        ],
        "Well1": [
            ["w1", "textfield", 2, None, None, "Name", None],
            ["w2", "email", 2, None, None, "Email", None],
        ],
    }


def _plotly_default_value():
    return {
        "data": [
            {
                "x": [-3, -2, -1, 0, 1, 2, 3],
                "y": [-3, -2, -1, 0, 1, 2, 3],
                "z": [
                    [6.6712802967174421e-5, 0.00337797214955247, -0.029870801373274684, -0.24495404057434964, -0.10995938332787396, -0.004314432616985781, -5.8641878725895287e-6],
                    [0.00074734337895483336, 0.046835385992884435, -0.59212842982359237, -4.7596121032136383, -2.1023512845906334, -0.061639793654092154, 0.00041822002330767167],
                    [-0.0087618924917887177, -0.13005295300439818, 1.8558917154077983, -0.72390617279329428, -0.27291654880625382, 0.49963628529592258, 0.013012486008918911],
                    [-0.03650620461319553, -1.3326904669589708, -1.6523454638655195, 0.98101184312384626, 2.9369303164086271, 1.4121612599396918, 0.033124949924308318],
                    [-0.01366906868116455, -0.48075877206514389, 0.22889945007177018, 3.6886295673017551, 2.4337891159260003, 0.58045469649513681, 0.012466690908012225],
                    [1.5488609851181312e-5, 0.079667927769172892, 2.0966790499089041, 5.8591286914741687, 2.2099347948240657, 0.13284922819447997, 0.0013202144463826647],
                    [3.2235359612692725e-5, 0.005305737765260379, 0.10991799007590233, 0.29987102822623468, 0.11068427531780239, 0.0056643866006954747, 4.1029727458267584e-5],
                ],
                "type": "contour",
                "contours": {"coloring": "lines", "showlabels": True},
                "line": {"width": 0.5, "dash": "solid"},
                "colorscale": [
                    [0, "#3E26A8FF"],
                    [0.2, "#4367FDFF"],
                    [0.4, "#1CAADFFF"],
                    [0.8, "#EABA30FF"],
                    [1, "#F9FB15FF"],
                ],
                "showscale": False,
            }
        ],
        "layout": {},
        "config": {"displaylogo": False},
        "styles": {
            "-": "solid",
            "--": "dash",
            "-.": "dashdot",
            ":": "dot",
            "none": "solid",
        },
    }  # fmt: skip


def _resultfile_default_value():
    file = str(Path(__file__).parent / "logo.png")
    url, fileName, fileSize = component._base64_encode(file, "image/png")

    return {
        "data": [
            {
                "name": fileName,
                "url": url,
                "size": component._determine_file_size(fileSize),
            }
        ]
    }
