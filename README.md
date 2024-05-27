## About

This project provides GUI (using PyQt5) for downloading music via Qobuz API.
It is based on the [qobuz-dl](https://github.com/vitiko98/qobuz-dl) created by vitiko98. I am not a UI expert, therefore I used [Tidal-Media-Downloader](https://github.com/yaronzz/Tidal-Media-Downloader) as inspiration.

## ☕ Support

If you really like my projects and want to support me, you can buy me a coffee and star this project.

[<img src="https://cdn.buymeacoffee.com/buttons/arial-orange.png">](https://www.buymeacoffee.com/yashock)

## Installation

First, install the necessary packages for GUI via pip.

`pip3 install .`

Then run using one of the following commands:

`qdlg` or `qobuz-dl-gui`

On first run a qobuz-dl based configuration is created, which can be modified either by hand or (in limited way) in the GUI config. If you run on Windows the configuration is located in AppData\Roaming\qobuz-dl, otherwise in home/user/.config/qobuz-dl

Upon running the program you have to log in with your Qobuz credentials. You can manually log out from config, or by deleting the config file.

## Developing

For development install the package in "editable" mode.

`pip3 install -e .`

To build a distributable run the following:

`pyinstaller gui.spec`

## Disclaimer

- This program is intended for private use only.
- You will a Qobuz subscription.
- I do not condone pirating music or any use of this software in bad faith.
- By using this software you are implicitly accepting the [Qobuz API Terms of Use](https://static.qobuz.com/apps/api/QobuzAPI-TermsofUse.pdf).
