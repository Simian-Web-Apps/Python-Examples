"""Bird swarm behavior module.

MonkeyProof Solutions demo application, for Simian exploration purposes.
Using particle swarm optimization to simulate a flock of birds looking for food.

The birds use both their own cognitive capabilities and 'the knowledge of group'
to identify the food, which is located on the highest point of the map.
The user is invited to tweak- and assess the impact of both cognitive and social
behavioral tuning parameters.

Copyright 2020-2024 MonkeyProof Solutions BV.
"""

import base64
import copy
import mimetypes
import os
import time
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from birdswarm import heightmap, pso_utils, swarm_animation
from birdswarm.pso_method import PSO
from scipy.interpolate import RegularGridInterpolator
from simian.gui import Form, component, utils


def gui_init(meta_data: dict) -> dict:
    # Create the form and load the json builder into it.
    Form.componentInitializer(app_pic_bird_food_frenzy=init_app_toplevel_pic)
    Form.componentInitializer(pso_pic_methodology=init_pic_pso_methodology)
    Form.componentInitializer(image=set_default_image)

    form = Form(from_file=__file__)
    examples_url = "https://github.com/Simian-Web-Apps/Python-Examples/"

    payload = {
        "form": form,
        "navbar": {
            "title": (
                f'<a class="text-white" href="{examples_url}" target="_blank">'
                '<i class="fa fa-github"></i></a>&nbsp;Data Science Demo: Particle Swarm Optimization'
            )
        },
    }

    return payload


def init_app_toplevel_pic(comp: component.HtmlElement):
    # Voeg depictie met titel toe in de linker bovenhoek.
    comp.setLocalImage(
        os.path.join(os.path.dirname(__file__), "app_pic.png"), scale_to_parent_width=True
    )
    comp.customClass = "px-5"


def init_pic_pso_methodology(comp: component.HtmlElement):
    # Voeg depictie met titel toe in web app body.
    comp.setLocalImage(
        os.path.join(os.path.dirname(__file__), "pso_pic.png"), scale_to_parent_width=True
    )
    comp.customClass = "px-5"


def set_default_image(comp: component.Hidden):
    comp.defaultValue = utils.encodeImage(
        os.path.join(os.path.dirname(__file__), "mehdi-sepehri-cX0Yxw38cx8-unsplash.jpg")
    )


def gui_event(meta_data: dict, payload: dict) -> dict:
    # Application event handler.
    Form.eventHandler(initialize_landscape_button=initiate_landscape)
    Form.eventHandler(calculate_button=calc_update)
    callback = utils.getEventFunction(meta_data, payload)

    return callback(meta_data, payload)


def initiate_landscape(meta_data: dict, payload: dict) -> dict:
    # Initiate landscape for bird swarm animation.
    map_size, _ = utils.getSubmissionData(payload, key="map_size")
    seed, _ = utils.getSubmissionData(payload, key="seed")
    octaves, _ = utils.getSubmissionData(payload, key="octaves")
    scale, _ = utils.getSubmissionData(payload, key="scale")
    expo, _ = utils.getSubmissionData(payload, key="expo")

    # Generate heightmap.
    X = np.arange(0, map_size)
    Y = np.arange(0, map_size)
    xg, yg = np.meshgrid(X, Y)
    zg = np.array(heightmap.generate_heightmap([map_size, map_size], seed, scale, expo, octaves))
    elevation_map = dict({"X": X, "Y": Y, "xg": xg, "yg": yg, "zg": zg})

    # Create the 2D and 3D terrain axes.
    plt.ioff()
    fig = plt.figure(frameon=True)
    ax_2d_plot = fig.add_subplot(1, 2, 1)
    ax_3d_plot = fig.add_subplot(1, 2, 2, projection="3d")

    pso_utils.plot_2d_pso_base(elevation_map, ax=ax_2d_plot)
    pso_utils.plot_3d_pso_base(elevation_map, ax=ax_3d_plot)

    # Store terrain in submission data.
    bufferImage = BytesIO()
    plt.savefig(bufferImage, format="png", dpi=100)
    terrain_fig_base64_data = base64.b64encode(bufferImage.getvalue()).decode("utf-8")
    image_format = mimetypes.guess_type("terrain.png")[0]
    terrain_fig_payload = f"data:{image_format};base64,{terrain_fig_base64_data}"

    payload, _ = utils.setSubmissionData(payload, "terrain_elevation_map", elevation_map)
    payload, _ = utils.setSubmissionData(payload, "image", terrain_fig_payload)

    return payload


def calc_update(meta_data: dict, payload: dict) -> dict:
    # Calculate and animate swarm behavior, based on user preferences.
    start_time = time.time()
    elevation_map, _ = utils.getSubmissionData(payload, key="terrain_elevation_map")

    if not elevation_map:
        # No elevation map available yet, stop and return.
        return payload

    # Fetch (behavioral) input variables.
    toggle_autotuning, _ = utils.getSubmissionData(payload, key="toggle_autotuning")
    map_size, _ = utils.getSubmissionData(payload, key="map_size")
    frames_per_second = utils.getSubmissionData(payload, key="frames_per_second")
    caption_rate = utils.getSubmissionData(payload, key="caption_rate")
    max_iterations, _ = utils.getSubmissionData(payload, key="max_iterations")
    max_birdspeed, _ = utils.getSubmissionData(payload, key="max_birdspeed")
    n_particles, _ = utils.getSubmissionData(payload, key="particles")
    omega, _ = utils.getSubmissionData(payload, key="omega")
    cognitive_weight, _ = utils.getSubmissionData(payload, key="cognitive_weight")
    social_weight, _ = utils.getSubmissionData(payload, key="social_weight")
    random_weigth, _ = utils.getSubmissionData(payload, key="random_weight")

    max_birdspeed = max_birdspeed / 3.6
    random_weigth = random_weigth / 100
    offset = 0.50

    frames_per_second = frames_per_second[0]
    caption_rate = caption_rate[0]

    # Create terrain image axes.
    plt.ioff()
    fig = plt.figure(frameon=True)
    ax_2d_plot = fig.add_subplot(1, 2, 1)
    ax_3d_plot = fig.add_subplot(1, 2, 2, projection="3d")

    pso_utils.plot_2d_pso_base(elevation_map, ax=ax_2d_plot)
    pso_utils.plot_3d_pso_base(elevation_map, ax=ax_3d_plot)

    # Assign initial positions and velocities.
    positions = np.random.uniform(0, np.size(elevation_map["X"]), (n_particles, 2))

    velocity_x = np.random.random(n_particles) * max_birdspeed
    velocity_y = np.sqrt(max_birdspeed**2 - velocity_x**2)
    velocity_sign = np.sign(np.random.uniform(-1, 1, (n_particles, 2)))
    velocities = np.multiply(np.hstack((velocity_x[:, None], velocity_y[:, None])), velocity_sign)

    # Instantiate and populate Particle Swarm Optimization object.
    # Define PSO fitness function, use interpolation:
    X = np.array(elevation_map["X"])
    Y = np.array(elevation_map["Y"])
    zz = np.array(elevation_map["zg"])
    map_interp = RegularGridInterpolator((X, Y), zz, bounds_error=False, fill_value=0.25)

    def fitness_function(pos, map_interp):
        return map_interp(pos)

    # Calculate swarm behavior and collect numeric results:
    pso = PSO(
        positions.copy(),
        velocities.copy(),
        max_birdspeed,
        map_size,
        map_interp,
        offset,
        fitness_function,
        omega,
        random_weigth,
        cognitive_weight,
        social_weight,
        max_iterations,
        toggle_autotuning,
    )

    positions, velocities, titles = pso.calculate(caption_rate)

    # Animate swarm behavior and return base64 encoded GIF content.
    animated_gif_payload = swarm_animation.build_animation(
        fig, map_interp, positions, velocities, offset, titles, frames_per_second
    )
    payload, _ = utils.setSubmissionData(payload, "image", animated_gif_payload)
    print("--- Animation time: %s seconds ---" % (time.time() - start_time))

    return payload


def capture_hold_scenario(meta_data: dict, payload: dict) -> dict:
    # Store the current submission data as "hold scenario".
    # Create a deep-copy of the submission data.
    submission_copy = copy.deepcopy(payload["submission"])
    payload, _ = utils.setSubmissionData(payload, "hold_submission_data", submission_copy)

    return payload


def restore_hold_scenario(meta_data: dict, payload: dict) -> dict:
    # Fetch stored payload and restore hold-scenario data.
    hold_submission_data, _ = utils.getSubmissionData(payload, key="hold_submission_data")

    if hold_submission_data:
        # Call update method and re-invoke hold().
        payload["submission"] = hold_submission_data
        payload = capture_hold_scenario(meta_data, payload)
        payload = calc_update(meta_data, payload)

    return payload


def clear_hold_scenario(meta_data: dict, payload: dict) -> dict:
    # Clear the stored "hold" submission data. Invoke update().
    hold_submission_data, _ = utils.getSubmissionData(payload, key="hold_submission_data")

    if hold_submission_data:
        payload, _ = utils.setSubmissionData(payload, "hold_submission_data", [])

    return payload
