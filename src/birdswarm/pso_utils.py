"""Particle Swarm Optimization, utilities package.

Source:
https://towardsdatascience.com/particle-swarm-optimization-visually-explained-46289eeb2e14

NOTE: modified to accomodate the use-case of a swarm of birds.

Author: Axel Thevenot.
Published in: Towards Data Science, Dec 21, 2020.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.ticker import FormatStrFormatter, LinearLocator

plt.rcParams["figure.figsize"] = [12, 6]  # default = [6.0, 4.0]
plt.rcParams["figure.dpi"] = 100  # default = 72.0
plt.rcParams["font.size"] = 7.5  # default = 10.0

cmap = cm.colors.LinearSegmentedColormap.from_list(
    "Custom", [(0, "#2f9599"), (0.45, "#eee"), (1, "#8800ff")], N=256
)


def plot_2d_pso_base(elev_map, ax=None):
    # Get coordinates and velocity arrays.
    xg = np.array(elev_map["xg"])
    yg = np.array(elev_map["yg"])
    zg = np.array(elev_map["zg"])

    # Add contours and contours lines.
    ax.contour(xg, yg, zg.T, levels=20, linewidths=0.5, colors="#999")
    ax.contourf(xg, yg, zg.T, levels=20, cmap=cmap, alpha=0.7)

    # Add labels and set equal aspect ratio.
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_xlim(np.min(xg), np.max(yg))
    ax.set_ylim(np.min(xg), np.max(yg))
    ax.set_aspect(aspect="equal")


def plot_3d_pso_base(elev_map, ax=None):
    # Get coordinates and velocity arrays.
    xg = np.array(elev_map["xg"])
    yg = np.array(elev_map["yg"])
    zg = np.array(elev_map["zg"])

    # Plot the surface and the scatter-plot depicting swarm position.
    ax.plot_surface(xg, yg, zg.T, cmap=cmap, linewidth=0, antialiased=True, alpha=0.7)
    len_space = 1

    # Customize the axis.
    max_z = (np.max(zg) // len_space + 1).astype(np.integer) * len_space
    ax.set_xlim3d(np.min(xg), np.max(xg))
    ax.set_ylim3d(np.min(yg), np.max(yg))
    ax.set_zlim3d(0, max_z)
    ax.zaxis.set_major_locator(LinearLocator(max_z // len_space + 1))
    ax.zaxis.set_major_formatter(FormatStrFormatter("%.0f"))

    # Remove fills and set labels.
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Height")
