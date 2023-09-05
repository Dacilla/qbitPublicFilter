import qbittorrentapi
import logging
import os
import configparser
import sys

from pprint import pprint

__VERSION = "1.0.0"
LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)-8s P%(process)06d.%(module)-12s %(funcName)-16sL%(lineno)04d %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def main():
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
            'DOWNLOAD_FOLDER': ''
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
    download_folder = config['DEFAULT']['DOWNLOAD_FOLDER']

    logging.info("Connecting to qbit instance at " + qbit_host)

    # Connect to qBittorrent Web UI
    qb = qbittorrentapi.Client(host=qbit_host,
                               username=qbit_username, password=qbit_password, REQUESTS_ARGS={'timeout': (60, 60)})
    # Authenticate and retrieve a list of torrents
    # qb.auth_log_in()

    logging.info("Logged in to qbit.")
    logging.info("Getting list of files in download directory: " + download_folder)
    existingFilesList = get_all_files(download_folder)
    logging.info("First 100 file paths: ")
    pprint(existingFilesList[:100])
    logging.info("Getting list of torrents...")
    torrents = qb.torrents_info(category=None, status_filter='completed')
    logging.info("Running through torrents to find orphaned files.")
    for torrent in torrents:
        try:
            torrentInfo = qb.torrents_files(torrent_hash=torrent['hash'])
            for file in torrentInfo:
                filePath = os.path.normpath(os.path.join(download_folder, file['name']))
                if not os.path.exists(filePath):
                    try:
                        existingFilesList.pop(existingFilesList.index(filePath))
                        logging.info("Removed file path that doesn't exist: " + filePath)
                    except ValueError:
                        continue
                logging.info("Looking for file: " + filePath)
                if filePath in existingFilesList:
                    logging.info("Matched file: " + filePath)
                    existingFilesList.pop(existingFilesList.index(filePath))
        except Exception as e:
            logging.warn("Exception hit: " + str(e) + ". Skipping...")
            continue
    logging.info("Orphaned files: ")
    pprint(existingFilesList)
    logging.info(f"{len(existingFilesList)} orphaned files found")
    with open('orphans.txt', 'w', encoding='utf-8') as f:
        for line in existingFilesList:
            f.write(f"{line}\n")
    logging.info("Written to orphans.txt")


def get_all_files(path):
    all_files = []
    count = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.normpath(os.path.join(root, file))
            all_files.append(full_path)
            count += 1
            print(f"\rFound {count} files...", end="")
    print("Done.")
    return all_files


if __name__ == "__main__":
    main()
