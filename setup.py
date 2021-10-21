from setuptools import setup

setup(
    name="scylla-cli",
    version="1.0",
    py_modules=["scylla_click"],
    include_package_data=True,
    install_requires=["click"],
    entry_points="""
        [console_scripts]
        scylla-cli=scylla_click:scylla_cli
    """,
)