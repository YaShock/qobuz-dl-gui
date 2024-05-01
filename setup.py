from setuptools import setup, find_packages

pkg_name = "qobuz-dl-gui"


def read_file(fname):
    with open(fname, "r") as f:
        return f.read()


requirements = [
    "pathvalidate",
    "requests",
    "mutagen",
    "tqdm",
    "pick==1.6.0",
    "beautifulsoup4",
    "colorama",
    "PyQt5",
    "qt-material",
]

setup(
    name=pkg_name,
    version="0.1",
    author="YaShock",
    author_email="jashok12@gmail.com",
    description="A GUI music downloader for Qobuz",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/YaShock/qobuz-dl-gui",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "qobuz-dl-gui = qobuz_dl_gui:main",
            "qdlg = qobuz_dl_gui:main",
        ],
    },
    packages=find_packages(include=["qobuz_dl_gui", "qobuz_dl_gui.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)