import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='fingerpaint',
    version='1.2.4',
    entry_points={
        'console_scripts': 'fingerpaint=fingerpaint.fingerpaint:cli'
    },
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
        'evdev >= 1.3.0',
        'Pillow >= 5.3.0',
        'pyudev'
    ],
    package_data={
        'fingerpaint': ['data/fix_permissions.sh'],
    },
)
