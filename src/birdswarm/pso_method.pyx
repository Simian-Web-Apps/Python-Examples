"""Particle Swarm Optimization, implementation class.

Source:
https://towardsdatascience.com/particle-swarm-optimization-visually-explained-46289eeb2e14

NOTE: modified to accomodate the use-case of a swarm of birds.

Author: Axel Thevenot.
Published in: Towards Data Science, Dec 21, 2020.
"""

import numpy as np


class PSO:
    def __init__(
        self,
        particles,
        velocities,
        max_velocity,
        map_size,
        map_interp,
        offset,
        fitness_function,
        w=0.5,
        r=0.015,
        c_1=1,
        c_2=1,
        max_iter=100,
        auto_coef=True,
    ):
        # Constructor.
        self.mapsize = map_size
        self.map_interp = map_interp
        self.offset = offset
        self.max_velocity = max_velocity

        self.fitness_function = fitness_function
        self.particles = particles
        self.velocities = velocities

        self.N = len(self.particles)
        self.w = w
        self.r = r
        self.c_1 = c_1
        self.c_2 = c_2
        self.auto_coef = auto_coef
        self.max_iter = max_iter

        self.p_bests = self.particles
        self.p_bests_values = self.fitness_function(self.particles, self.map_interp)
        best_p_ind = np.argmax(self.p_bests_values)

        self.p_best_cnt = 0
        self.g_best = self.p_bests[best_p_ind]
        self.g_best_value = np.max(self.p_bests_values)
        self.update_bests()

        self.iter = 0
        self.is_running = True
        self.update_coef()

    def __str__(self):
        return f"[{self.iter}/{self.max_iter}] $w$:{self.w:.3f} - $c_1$:{self.c_1:.3f} - $c_2$:{self.c_2:.3f} - $r$:{self.r*100:.3f}"

    def calculate(self, caption_rate):
        positions = []
        velocities = []
        frame_titles = []

        while self.next():
            # Loop over iterations.
            if self.iter % caption_rate == 0:
                # Add 2D and 3D frame plots.
                positions.append(self.particles)
                velocities.append(self.velocities)
                frame_titles.append(str(self))

        return positions, velocities, frame_titles

    def next(self):
        if self.iter > 0:
            self.move_particles()
            self.update_bests()
            self.update_coef()

        self.iter += 1
        self.is_running = self.is_running and self.iter < self.max_iter

        return self.is_running

    def update_coef(self):
        if self.auto_coef:
            # Complete auto-calibration in half the amount of iterations.
            t = self.iter
            n = self.max_iter
            n = np.maximum(0.5 * self.max_iter, 250)

            self.r = 0
            self.c_1 = -3 * np.minimum(t / n, 1) + 3.5
            self.c_2 = 3 * np.minimum(t / n, 1) + 0.5

            # Disabled: birds have constant weight.
            # self.w = (0.4/n**2) * (t - n) ** 2 + 0.4

    def move_particles(self):
        # Add inertia speed component.
        new_velocity_inertia = self.w * self.velocities

        # Add random speed component.
        velocity_x = np.random.random(self.N) * self.max_velocity
        velocity_y = np.sqrt(self.max_velocity**2 - velocity_x**2)
        velocity_sign = np.sign(np.random.uniform(-1, 1, (self.N, 2)))
        new_velocity_random = self.r * np.multiply(
            np.hstack((velocity_x[:, None], velocity_y[:, None])), velocity_sign
        )

        # Add cognitive speed component.
        r_1 = np.random.random(self.N)
        r_1 = np.tile(r_1[:, None], (1, 2))
        new_velocity_cognitive = self.c_1 * r_1 * (self.p_bests - self.particles) / self.mapsize

        # Add social speed component.
        r_2 = np.random.random(self.N)
        r_2 = np.tile(r_2[:, None], (1, 2))
        g_best = np.tile(self.g_best[None], (self.N, 1))
        new_velocity_social = self.c_2 * r_2 * (g_best - self.particles) / self.mapsize

        # Update positions and velocities.
        # Enforce max velocity conditions.
        new_velocities = (
            new_velocity_inertia
            + new_velocity_random
            + new_velocity_cognitive
            + new_velocity_social
        )
        net_velocities = np.sqrt(new_velocities[:, 0] ** 2 + new_velocities[:, 1] ** 2)
        exceed_velocity = net_velocities > self.max_velocity

        if any(exceed_velocity):
            new_velocities[exceed_velocity] = new_velocities[exceed_velocity] * (
                self.max_velocity / net_velocities[exceed_velocity].reshape(-1, 1)
            )

        self.is_running = np.sum(self.velocities - new_velocities) != 0
        self.velocities = new_velocities
        self.particles = self.particles + new_velocities

    def update_bests(self):
        # Updating best results.
        fits = self.fitness_function(self.particles, self.map_interp)

        for ii in range(len(self.particles)):
            # Update best personnal value (cognitive).
            if fits[ii] > self.p_bests_values[ii]:
                self.p_bests_values[ii] = fits[ii]
                self.p_bests[ii] = self.particles[ii]
                self.p_best_cnt += 1

            # Update best global value (social).
            if fits[ii] > self.g_best_value:
                self.g_best_value = fits[ii]
                self.g_best = self.particles[ii]
