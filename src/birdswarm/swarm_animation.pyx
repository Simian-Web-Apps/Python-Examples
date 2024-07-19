"""Particle Swarm Optimization, animation package.

Copyright 2020-2024 MonkeyProof Solutions BV.
"""

import base64
import io
import mimetypes
import os
import tempfile

import matplotlib.animation as animation
import numpy as np


def build_animation(fig, map_interp, positions, velocities, offset, titles, frames_per_second):
    # Declare animation frame update function.
    plot1_base_children = fig.axes[0].get_children()
    plot2_base_children = fig.axes[1].get_children()

    def update(ii):
        # Collect 2D and 3D frame plots.
        plot1_current_children = fig.axes[0].get_children()
        plot2_current_children = fig.axes[1].get_children()
        plot1_frame_plots = [x for x in plot1_current_children if x not in plot1_base_children]
        plot2_frame_plots = [x for x in plot2_current_children if x not in plot2_base_children]

        # Remove previous frameplot from reusable axes.
        for frameplot in plot1_frame_plots:
            frameplot.remove()
        for frameplot in plot2_frame_plots:
            frameplot.remove()

        plot_2d_pso_update(np.array(positions[ii]), np.array(velocities[ii]), ax=fig.axes[0])
        plot_3d_pso_update(map_interp, np.array(positions[ii]), offset, ax=fig.axes[1])
        fig.axes[0].set_title(titles[ii])

        return (fig.axes[0], fig.axes[1])

    # Write animation results to memory, using a tempfile.
    swarm_animation = animation.FuncAnimation(
        fig=fig, func=update, repeat=True, frames=len(positions), interval=1
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".gif") as temp_file:
        # Read the file contents into a BytesIO object
        writer = animation.PillowWriter(
            fps=frames_per_second, metadata=dict(artist="Me"), bitrate=-1
        )
        swarm_animation.save(temp_file.name, writer=writer)
        temp_file.seek(0)
        animated_gif = io.BytesIO(temp_file.read())

    # Delete the temporary file upon completion.
    os.remove(temp_file.name)

    # Store animation in submission data.
    animated_gif_base64_data = base64.b64encode(animated_gif.getvalue()).decode("utf-8")
    image_format = mimetypes.guess_type("animation.gif")[0]
    animated_gif_payload = f"data:{image_format};base64,{animated_gif_base64_data}"

    # Return base64 encoded animation.
    return animated_gif_payload


def plot_2d_pso_update(positions=None, velocities=None, normalize=True, color="#000", ax=None):
    # Get coordinates and velocity arrays.
    plot_2d_quiver = None

    if positions is not None:
        X, Y = positions.swapaxes(0, 1)

        if velocities is not None:
            U, V = velocities.swapaxes(0, 1)

            if normalize:
                N = np.sqrt(U**2 + V**2)
                U, V = U / N, V / N

            plot_2d_quiver = ax.quiver(
                X, Y, U, V, color=color, headwidth=2, headlength=2, width=5e-3
            )

    return plot_2d_quiver


def plot_3d_pso_update(map_interp, positions=None, offset=0.5, color="#000", ax=None):
    # Get coordinates and velocity arrays.
    plot_3d_scatter = None

    if positions is not None:
        X, Y = positions.swapaxes(0, 1)
        Z = map_interp(positions) + offset

        if positions is not None:
            plot_3d_scatter = ax.scatter(X, Y, Z, color=color, depthshade=True)

    return plot_3d_scatter
