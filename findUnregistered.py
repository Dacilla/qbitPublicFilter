import qbittorrentapi
import logging
import os
import configparser
import sys

from pprint import pprint
from urllib.parse import urlparse

__VERSION = "1.0.0"
LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)-8s P%(process)06d.%(module)-12s %(funcName)-16sL%(lineno)04d %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def extract_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]  # Remove 'www.' if it exists
    return domain


logging.basicConfig(datefmt=LOG_DATE_FORMAT,
                    format=LOG_FORMAT, level=logging.INFO)
logging.info(f"Version {__VERSION} starting...")

if not os.path.exists('settings.ini'):
    logging.info("No settings.ini file found. Generating...")
    config = configparser.ConfigParser()

    config['DEFAULT'] = {
        'QBIT_USERNAME': '',
        'QBIT_PASSWORD': '',
        'QBIT_HOST': '',
        'UNREGISTERED_TAG': ''
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
unregistered_tag = config['DEFAULT']['UNREGISTERED_TAG']
if unregistered_tag is None or unregistered_tag == '':
    unregistered_tag = 'Unregistered'

logging.info("Connecting to qbit instance at " + qbit_host)

# Connect to qBittorrent Web UI
qb = qbittorrentapi.Client(host=qbit_host,
                           username=qbit_username, password=qbit_password, REQUESTS_ARGS={'timeout': (120, 120)})
# Authenticate and retrieve a list of torrents
# qb.auth_log_in()

logging.info("Logged in to qbit.")
logging.info("Getting list of categories...")
categories = qb.torrent_categories.categories.keys()
foundTorrents = []
for category in categories:
    attempts = 0
    readSuccess = False
    torrents = None
    logging.info("Reading category: " + category)
    while not readSuccess or not torrents:
        if attempts < 5:
            try:
                if attempts != 0:
                    logging.info("Attempt " + attempts)
                torrents = qb.torrents_info(category=category, status_filter='completed')
            except Exception:
                logging.error("Got kicked. Retrying...")
                qb = qbittorrentapi.Client(host=qbit_host,
                                           username=qbit_username, password=qbit_password, REQUESTS_ARGS={'timeout': (120, 120)})
                attempts += 1
                continue
        else:
            logging.info("Run out of attempts. Exiting.")
            sys.exit()
        readSuccess = True
    logging.info("Running through torrents to find unregistered torrents.")
    # Filter for public torrents
    for counter, torrent in enumerate(torrents):
        try:
            trackersInfo = qb.torrents_trackers(torrent_hash=torrent['hash'])
            unregisteredTorrents = []
            if trackersInfo[0]['msg'] == 'This torrent is private':
                for tracker in trackersInfo:
                    if tracker['msg'] != 'This torrent is private' and tracker['msg'] not in ['', 'skipping tracker announce (unreachable)', 'Forbidden']:
                        foundTorrents.append(torrent['name'] + " - " + extract_domain(tracker['url']) + ' - ' + tracker['msg'])
                        unregisteredTorrents.append(torrent['hash'])
                        break
                    # if 'unregistered' in tracker['msg'].lower():
                    #     logging.info("Unregistered torrent found with name: " + torrent['name'])
                    #     foundTorrents.append(torrent['name'])
                    #     break
            print("Run through " + str(counter) + " torrents, finding " + str(len(foundTorrents)) + " unregistered torrents", end="\r")
        except qbittorrentapi.NotFound404Error:
            logging.error("No torrent found for hash: " + torrent['hash'] + ". Skipping...")
            continue
        except Exception as e:
            logging.error(f"Error: {e}")
            logging.error("Auth error. Skipping to try again...")
            continue

logging.info(f"Found {len(foundTorrents)} torrents")
unregisteredFile = "UnregisteredTorrents.txt"
logging.info("Adding unregistered to " + unregisteredFile)
logging.info(f"Adding '{unregistered_tag}' tag to found torrents")
pprint(unregisteredTorrents)
qb.torrents_add_tags(unregistered_tag, unregisteredTorrents)
logging.info(f"Tag '{unregistered_tag}' added to torrents")

with open(unregisteredFile, 'w', encoding='utf-8') as file:
    foundTorrents.sort()
    for line in foundTorrents:
        file.write(line + "\n")
# logging.info("All public torrents: ")
# pprint(publicTorrentsList)
