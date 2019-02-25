"""Setup."""

try:
    from setuptools import setup
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from distutils.core import setup  # pylint: disable=wrong-import-order

with open('README.md') as f:
    long_description = f.read()  # pylint: disable=invalid-name

test_deps = [
    'pytest',
]
extras = {
    'test': test_deps,
}

setup(
    author='Soar Technology, Inc.',
    name='statick-rosm-registry',
    description='Statick extension to generate files for the ROS-M registry.',
    version='0.1.1',
    packages=['statick_tool', 'statick_tool.plugins.reporting.rosm_registry_plugin'],
    package_dir={'statick_tool.plugins.reporting.rosm_registry_plugin': 'rosm_registry_plugin',
                 'statick_tool': '.'},
    package_data={'statick_tool.plugins.reporting.rosm_registry_plugin': ['*.yapsy-plugin'],
                  'statick_tool': ['rsc/*']},
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['statick'],
    tests_require=test_deps,
    extras_require=extras,
    url='https://github.com/soartech/statick-rosm-registry',
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Testing",
    ],
)
