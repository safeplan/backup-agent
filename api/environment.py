"""Safeplan environment"""
import os
import logging
import requests
from pathlib import Path
from datetime import datetime
from dateutil import tz

LOGGER = logging.getLogger()

SAFEPLAN_DEVICE_BASE_PATH = os.environ.get("SAFEPLAN_DEVICE_BASE_PATH", "/var/safeplan")

PATH_BACKUP = "{}/backup".format(SAFEPLAN_DEVICE_BASE_PATH)
PATH_CONFIG = "{}/config".format(SAFEPLAN_DEVICE_BASE_PATH)
PATH_MOUNTPOINT = "{}/history/backups".format(SAFEPLAN_DEVICE_BASE_PATH)
PATH_WORK = "{}/work".format(SAFEPLAN_DEVICE_BASE_PATH)
PATH_SSH = os.path.join(str(Path.home()), ".ssh")

FILENAME_BORG_PASSPHRASE = "{}/config/borg_passphrase".format(SAFEPLAN_DEVICE_BASE_PATH)
FILENAME_DEVICE_SECRET = "{}/config/device_secret".format(SAFEPLAN_DEVICE_BASE_PATH)
FILENAME_PRIVATE_KEY = os.path.join(PATH_SSH, "id_rsa")
FILENAME_PUBLIC_KEY = os.path.join(PATH_SSH, "id_rsa.pub")
FILENAME_IP_ADDRESS = os.path.join(PATH_CONFIG, "ipaddress")
SAFEPLAN_SSH = "safeplan-device@backup.safeplan.at:2222"

FORCED_MODE = os.environ.get("FORCED_MODE")

EXECUTE_WORKER_EVERY_SECONDS = 60

MAX_AGE_SECONDS = 12 * 3600


def check_paths():
    if not os.access(PATH_BACKUP, os.W_OK):
        return False, PATH_BACKUP

    if not os.access(FILENAME_DEVICE_SECRET, os.R_OK):
        return False, FILENAME_DEVICE_SECRET

    if not os.access(PATH_CONFIG, os.W_OK):
        return False, PATH_CONFIG

    if not os.access(PATH_WORK, os.W_OK):
        return False, PATH_WORK

    return True, None


def is_online():
    # Checks if the environment is OK so that the safeplan agent can operate
    return try_connect("https://safeplan.at") or try_connect("https://google.at")


def try_connect(url):
    # Returns true if the connect was successful
    try:
        requests.get(url)
        return True
    except requests.exceptions.RequestException:
        LOGGER.error("Failed to connect to %s", url)
        return False


def get_ip_address():
    """
    Returns the IP address provided by the ipaddress file located in the config path

    on a safeplan device, set it as follows
    $(ip -4 addr show eth0| grep -Po 'inet \K[\d.]+') > ipadress
    """

    if os.path.exists(FILENAME_IP_ADDRESS):
        with open(FILENAME_IP_ADDRESS, 'r') as file:
            ip_address = file.read()
            if len(ip_address) > 0:
                return ip_address.strip()

    return 'localhost'


def get_cc_api_key():
    return os.environ.get('CC_API_KEY')


def get_safeplan_id():
    """
    Returns the assigned safeplan id
    """

    if not 'SAFEPLAN_ID' in os.environ or os.environ['SAFEPLAN_ID'] == 'NOT_SET':
        return None

    return os.environ['SAFEPLAN_ID']


def get_rsa_public_key():
    """
    Returns the device's public key
    """
    with open(FILENAME_PUBLIC_KEY, 'r') as file:
        return file.read()


def get_borg_passphrase():
    """
    Returns the device's public key
    """
    with open(FILENAME_BORG_PASSPHRASE, 'r') as file:
        return file.read()


def get_device_secret():
    """
    Returns the device's public key
    """

    if os.path.exists(FILENAME_DEVICE_SECRET):
        with open(FILENAME_DEVICE_SECRET, 'r') as file:
            return file.read().strip()

    return None


def get_current_mode():
    """
    backup 00:00-4:00, cleanup 05:00-06:00, idle otherwise
    """

    if int(datetime.now().hour) >= 0 and int(datetime.now().hour) < 4:
        return 'backup'
    elif int(datetime.now().hour) >= 5 and int(datetime.now().hour) < 6:
        return 'cleanup'
    else:
        return 'idle'


def set_forced_mode(mode):
    global FORCED_MODE
    FORCED_MODE = mode


def get_forced_mode():
    global FORCED_MODE
    return FORCED_MODE


def get_ssh_key_path():
    return PATH_SSH
