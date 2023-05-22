import setuptools
import re

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("pyproject.toml", "r") as fh:
    pyproject = fh.read()
    pyproject_version = re.search(r'version = "(.*)"', pyproject).group(1)

setuptools.setup(
    name="fingerpaint",
    version=pyproject_version,
    entry_points={"console_scripts": "fingerpaint=fingerpaint.fingerpaint:cli"},
    author="David Shlemayev",
    author_email="david.shlemayev@gmail.com",
    description="Draw using your laptop's touchpad",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Wazzaps/fingerpaint",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Environment :: X11 Applications",
        "Operating System :: POSIX :: Linux",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Artistic Software",
        "Topic :: Multimedia :: Graphics :: Editors :: Raster-Based",
        "Topic :: Utilities",
    ],
    install_requires=[
        "evdev >= 1.6.1",
        "pyudev >= 0.24.0",
        "PyGObject >= 3.44.1",
    ],
    package_data={
        "fingerpaint": ["data/fix_permissions.sh"],
    },
    python_requires=">=3.7",
)
