from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
except ImportError as exc:
    raise RuntimeError("Cython is required to build Class 4.") from exc


extensions = [
    Extension(
        "class4_app._heat",
        ["src/class4_app/_heat.pyx"],
    )
]


setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
    ),
)
