from setuptools import setup, Extension

# Fast AST analyzer C++ extension
fast_ast_module = Extension(
    'backend.tracer.fast_ast',
    sources=['backend/tracer/fast_ast.cpp'],
    include_dirs=[],  # Add Python include dirs
    library_dirs=[],
    libraries=[],
    extra_compile_args=['-std=c++17', '-O3'],  # Optimization flags
    extra_link_args=[],
    language='c++'
)

setup(
    name='code-archaeologist-fast-ast',
    version='0.1.0',
    description='Fast C++ AST analyzer for Code Archaeologist',
    ext_modules=[fast_ast_module],
    packages=[],  # Don't discover packages
    py_modules=[],  # Don't discover modules
    python_requires='>=3.8',
)