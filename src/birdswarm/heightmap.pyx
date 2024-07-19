"""Heightmap creation module.

Use for Bird swarm behavior demo application, for Simian exploration purposes:
Particle swarm optimization based simulation of a flock of birds looking for food.

Source:
https://loady.one/blog/terrain_mesh.html

MIT License
Copyright (c) 2019 Oldřich Pecák
"""

import noise
import numpy as np


def update_point(map_size, coords, seed, scale, octaves):
    return noise.snoise2(
        coords[0] / scale,
        coords[1] / scale,
        octaves=octaves,
        persistence=0.5,
        lacunarity=2,
        repeatx=map_size[0],
        repeaty=map_size[1],
        base=seed,
    )


def normalize(map_size, input_map, minimum, maximum, expo):
    scale = maximum - minimum
    output_map = np.zeros(map_size)

    for x in range(map_size[0]):
        for y in range(map_size[1]):
            output_map[x][y] = ((input_map[x][y] - minimum) / scale) ** expo

    return output_map


def generate_heightmap(map_size, seed, scale, expo, octaves):
    minimum = 0
    maximum = 0
    heightmap = np.zeros(map_size)

    for x in range(map_size[0]):
        for y in range(map_size[1]):
            new_value = update_point(map_size, (x, y), seed, scale, octaves)
            heightmap[x][y] = new_value

            if new_value < minimum:
                minimum = new_value
            if new_value > maximum:
                maximum = new_value

    return normalize(map_size, heightmap, minimum, maximum, expo)
