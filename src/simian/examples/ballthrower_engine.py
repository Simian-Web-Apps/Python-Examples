"""Ballthrower class. Implements the functional model.

Copyright 2020-2023 MonkeyProof Solutions BV.
"""

import numpy as np
from scipy.integrate import solve_ivp


class BallThrower:
    """Ballthrower class. Implements the functional model."""

    @staticmethod
    def throw_ball(
        x0: float = 0,
        y0: float = 0,
        u0: float = 10,
        v0: float = 10,
        Cd: float = 0.4,
        r: float = 0.05,
        rho: float = 1.239,
        g: float = -9.81,
        m: float = 0.1,
        w: float = 0,
    ) -> list:
        """Ball thrower solver.

        Args:
            x0:     Initial horizontal location [m]. Defaults to 0.
            y0:     Initial vertical location [m]. Defaults to 0.
            u0:     Initial horizontal speed [m/s]. Defaults to 10.
            v0:     Initial vertical speed [m/s]. Defaults to 10.
            Cd:     Drag coefficient of the ball [-]. Defaults to 0.4.
            r:      Radius of the ball [m]. Defaults to 0.05.
            rho:    Air density [kg/m3]. Defaults to 1.239.
            g:      Gravitational pull [m/s2]. Defaults to -9.81.
            m:      Mass of the ball [kg]. Defaults to 0.1.
            w:      Wind speed [m/s]. Defaults to 0.

        Returns:
            t:      Time stamps (in seconds).
            x:      Horizontal distance travelled over time (in meters).
            y:      Vertical distance travelled over time (in meters).
            u:      Horizontal speed over time (in meters per second).
            v:      Vertical speed over time (in meters per second).
        """
        # Define the zero crossing function that should abort the simulation.
        def _zero_crossing(_t, y, *_args):
            return y[2]
        
        # Ensure that gravity is pointing downwards.
        g = abs(g) * -1

        _zero_crossing.terminal = True
        _zero_crossing.direction = -1

        # Solve the differential equation.
        outputs = solve_ivp(
            fun=BallThrower._drag_ball,
            t_span=[0, np.Inf],
            y0=[x0, u0, y0, v0],
            events=_zero_crossing,
            args=(Cd, r, rho, g, m, w),
            rtol=1e-8,
            atol=1e-8,
            max_step=0.1,
        )

        t = outputs.t
        y = outputs.y

        # Return the time stamps, location and speed components.
        return t, y[0], y[2], y[1], y[3]

    @staticmethod
    def _drag_ball(
        _t: float, y: list, Cd: float, r: float, rho: float, g: float, m: float, w: float
    ) -> list:
        """Calculates the location and speed of the ball at time step t.

        Args:
            t:      Time stamp.
            y:      The location and speed of the ball at time stamp t - 1.
            Cd:     Drag coefficient of the ball [-].
            r:      Radius of the ball [m].
            rho:    Air density [kg/m3].
            g:      Gravitational pull [m/s2].
            m:      Mass of the ball [kg].
            w:      Wind speed [m/s].

        Returns:
            y:      List of dx/dt, du/dt, dy/dt and dv/dt values.
        """
        A = np.pi * r**2

        return [
            y[1],
            -0.5 * rho / m * (y[1] - w) ** 2 * Cd * A * np.sign(y[1] - w),
            y[3],
            -0.5 * rho / m * y[3] ** 2 * Cd * A * np.sign(y[3]) + g,
        ]
