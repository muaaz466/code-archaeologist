"""
Setup script for building C++ extensions with pybind11
"""
from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11
from setuptools import setup, Extension
import sys
import platform

# Determine platform-specific settings
if platform.system() == "Windows":
    extra_compile_args = ['/std:c++17', '/O2']
    extra_link_args = []
elif platform.system() == "Darwin":  # macOS
    extra_compile_args = ['-std=c++17', '-O3', '-fPIC', '-stdlib=libc++']
    extra_link_args = ['-stdlib=libc++']
else:  # Linux
    extra_compile_args = ['-std=c++17', '-O3', '-fPIC']
    extra_link_args = []

ext_modules = [
    Pybind11Extension(
        "backend.graph.fast_graph",
        sources=[
            "backend/graph/cpp/bindings/graph_bindings.cpp",
            "backend/graph/cpp/src/fast_graph.cpp",
        ],
        include_dirs=[
            "backend/graph/cpp/include",
            pybind11.get_include(),
        ],
        cxx_std=17,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    name="code-archaeologist",
    version="1.0.0",
    author="Code Archaeologist Team",
    description="Fast C++ graph engine for code analysis",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
)
