import qbittorrentapi
import logging
import os
import configparser
import sys

from pprint import pprint

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
                           username=qbit_username, password=qbit_password, REQUESTS_ARGS={'timeout': (60, 60)})
# Authenticate and retrieve a list of torrents
# qb.auth_log_in()

logging.info("Logged in to qbit.")
logging.info("Getting list of torrents...")

attempts = 0
readSuccess = False
torrents = None
while not readSuccess or not torrents:
    if attempts < 5:
        try:
            if attempts != 0:
                logging.info("Attempt " + attempts)
            torrents = qb.torrents_info(category='radarr', status_filter='completed')
        except Exception:
            logging.error("Got kicked. Retrying...")
            attempts += 1
            continue
    else:
        logging.info("Run out of attempts. Exiting.")
        sys.exit()
    readSuccess = True
logging.info("Running through torrents to find public torrents.")
# Filter for public torrents
publicTorrentsList = []
for torrent in torrents:
    try:
        torrentInfo = qb.torrents_trackers(torrent_hash=torrent['hash'])
    except qbittorrentapi.NotFound404Error:
        logging.error("No torrent found for hash: " + torrent['hash'] + ". Skipping...")
        continue
    except Exception:
        logging.error("Auth error. Skipping to try again...")
        continue
    try:
        # if torrentInfo[0]['msg'] != 'This torrent is private' or ('hawke.uno' not in torrentInfo[3]['url'] and 'xtremewrestling' not in torrentInfo[3]['url']):
        #     publicTorrentsList.append(torrent)
        #     logging.info("Public torrent found: " + torrent['name'])
        #     logging.info("Throttling upload for hash: " + torrent['hash'])
        #     qb.torrents_set_upload_limit(limit=20000, torrent_hashes=torrent['hash'])
        if torrentInfo[0]['msg'] == 'This torrent is private':
            # publicTorrentsList.append(torrent)
            logging.info("Private torrent found: " + torrent['name'])
            # logging.info("Unthrottling upload for hash: " + torrent['hash'])
            # qb.torrents_set_upload_limit(limit=-1, torrent_hashes=torrent['hash'])
        else:
            logging.info("Public torrent found: " + torrent['name'])
            logging.info("Throttling upload for hash: " + torrent['hash'])
            qb.torrents_set_upload_limit(limit=10000, torrent_hashes=torrent['hash'])
    except Exception:
        logging.warning("Failed to set upload limit. Skipping...")
        continue


logging.info("All public torrents throttled")
# logging.info("All public torrents: ")
# pprint(publicTorrentsList)
