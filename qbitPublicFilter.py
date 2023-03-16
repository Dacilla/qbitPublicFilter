import qbittorrentapi
import logging
import os
import configparser
import sys

__VERSION = "1.0.0"
LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)-8s P%(process)06d.%(module)-12s %(funcName)-16sL%(lineno)04d %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


logging.basicConfig(datefmt=LOG_DATE_FORMAT,
                    format=LOG_FORMAT, level=logging.INFO)
logging.info(f"Version {__VERSION} starting...")

if not os.path.exists('settings.ini'):
    logging.info("No settings.ini file found. Generating...")
    config = configparser.ConfigParser()

    config['DEFAULT'] = {
        'QBIT_USERNAME': '',
        'QBIT_PASSWORD': '',
        'QBIT_HOST': ''
    }

    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

    sys.exit("settings.ini file generated. Please fill out before running again")

# Load the INI file
config = configparser.ConfigParser()
config.read('settings.ini')
qbit_username = config['DEFAULT']['QBIT_USERNAME']
qbit_password = config['DEFAULT']['QBIT_PASSWORD']
qbit_host = config['DEFAULT']['QBIT_HOST']

logging.info("Connecting to qbit instance at " + qbit_host)

# Connect to qBittorrent Web UI
qb = qbittorrentapi.Client(host=qbit_host,
                           username=qbit_username, password=qbit_password, VERBOSE_RESPONSE_LOGGING=True)
# Authenticate and retrieve a list of torrents
# qb.auth_log_in()

logging.info("Logged in to qbit.")
logging.info("Getting list of torrents...")
torrents = qb.torrents_info(category=None, status_filter='completed')

logging.info("Running through torrents to find public torrents.")
# Filter for public torrents
public_torrents = [torrent for torrent in torrents if torrent.is_public]
print(public_torrents)
# Print the list of public torrents
for torrent in public_torrents:
    print(torrent.name)
