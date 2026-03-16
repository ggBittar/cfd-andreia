from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
except ImportError as exc:
    raise RuntimeError("Cython is required to build Class 2 - versao 2.") from exc


extensions = [
    Extension(
        "class2_v2_app._burgers",
        ["src/class2_v2_app/_burgers.pyx"],
    )
]


setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
    ),
)
