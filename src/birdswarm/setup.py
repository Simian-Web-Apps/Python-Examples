from Cython.Build import cythonize
from setuptools import setup

setup(
    ext_modules=cythonize(
        [
            "pso_method.pyx",
            "heightmap.pyx",
            "swarm_animation.pyx",
        ]
    )
)
