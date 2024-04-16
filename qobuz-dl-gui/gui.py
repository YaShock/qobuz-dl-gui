import sys
import os
import logging
import configparser
import hashlib

from PyQt5 import QtWidgets
from qt_material import apply_stylesheet

from qobuz_dl.bundle import Bundle
from qobuz_dl.color import GREEN, RED, YELLOW
from qobuz_dl.core import QobuzDL
from qobuz_dl.downloader import DEFAULT_FOLDER, DEFAULT_TRACK

from login import Login
from main_view import MainView


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

if os.name == "nt":
    OS_CONFIG = os.environ.get("APPDATA")
else:
    OS_CONFIG = os.path.join(os.environ["HOME"], ".config")

CONFIG_PATH = os.path.join(OS_CONFIG, "qobuz-dl")
CONFIG_FILE = os.path.join(CONFIG_PATH, "config.ini")
# QOBUZ_DB = os.path.join(CONFIG_PATH, "qobuz_dl.db")


# TODO: pull request to qobuz dl to create a default config from email/pass
def reset_config(config_file):
    logging.info(f"{YELLOW}Creating config file: {config_file}")
    config = configparser.ConfigParser()
    config["DEFAULT"]["email"] = ""
    config["DEFAULT"]["password"] = ""
    config["DEFAULT"]["default_folder"] = "Qobuz Downloads"
    config["DEFAULT"]["default_quality"] = "6"
    config["DEFAULT"]["default_limit"] = "20"
    config["DEFAULT"]["no_m3u"] = "false"
    config["DEFAULT"]["albums_only"] = "false"
    config["DEFAULT"]["no_fallback"] = "false"
    config["DEFAULT"]["og_cover"] = "false"
    config["DEFAULT"]["embed_art"] = "false"
    config["DEFAULT"]["no_cover"] = "false"
    config["DEFAULT"]["no_database"] = "false"
    logging.info(f"{YELLOW}Getting tokens. Please wait...")
    bundle = Bundle()
    config["DEFAULT"]["app_id"] = str(bundle.get_app_id())
    config["DEFAULT"]["secrets"] = ",".join(bundle.get_secrets().values())
    config["DEFAULT"]["folder_format"] = DEFAULT_FOLDER
    config["DEFAULT"]["track_format"] = DEFAULT_TRACK
    config["DEFAULT"]["smart_discography"] = "false"
    with open(config_file, "w") as configfile:
        config.write(configfile)
    logging.info(
        f"{GREEN}Config file updated. Edit more options in {config_file}"
        "\nso you don't have to call custom flags every time you run "
        "a qobuz-dl command."
    )


def check_config_init():
    if not os.path.isdir(CONFIG_PATH) or not os.path.isfile(CONFIG_FILE):
        os.makedirs(CONFIG_PATH, exist_ok=True)
        reset_config(CONFIG_FILE)


# TODO: create settings that will save the input
def login():
    login_window = Login()

    # TODO: create config if it doesn't exist yet
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        email = config["DEFAULT"]["email"]
        password = config["DEFAULT"]["password"]
    except (KeyError, UnicodeDecodeError, configparser.Error) as error:
        logging.info(f"{RED}Your config file is corrupted: {error}!")
        return

    if email == "" or password == "":
        if login_window.exec_() == QtWidgets.QDialog.Accepted:
            email = login_window.text_email.text()
            password = login_window.text_pass.text()

            config["DEFAULT"]["email"] = email
            config["DEFAULT"]["password"] = hashlib.md5(
                password.encode("utf-8")).hexdigest()
            # TODO: check credentials
            with open(CONFIG_FILE, "w") as configfile:
                config.write(configfile)

            # email = "kobuzmisilevi@gmail.com"
            # password = "Kobuz777!"
    qobuz = QobuzDL()
    qobuz.get_tokens() # get 'app_id' and 'secrets' attrs
    qobuz.initialize_client(email, password, qobuz.app_id, qobuz.secrets)
    return qobuz


def start_gui():
    app = QtWidgets.QApplication(sys.argv)
    apply_stylesheet(app, theme='theme.xml')
    # apply_stylesheet(app, theme='dark_cyan.xml')

    check_config_init()

    # TODO make a login window
    qobuz = login()
    if qobuz:
        window = MainView(qobuz)
        window.show()
        # window.checkLogin()
        app.exec_()


if __name__ == '__main__':
    start_gui()
