import logging
from qobuz_dl.core import QobuzDL

logging.basicConfig(level=logging.INFO)

email = "kobuzmisilevi@gmail.com"
password = "Kobuz777!"

qobuz = QobuzDL()
qobuz.get_tokens() # get 'app_id' and 'secrets' attrs
qobuz.initialize_client(email, password, qobuz.app_id, qobuz.secrets)

qobuz.handle_url("https://play.qobuz.com/album/va4j3hdlwaubc")
