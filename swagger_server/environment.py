"""Safeplan environment"""
import logging
import requests

LOGGER = logging.getLogger("environment")

PATH_BACKUP = "/var/safeplan/backup"
PATH_CONFIG = "/var/safeplan/backup/.safeplan"


def is_online():
    """Checks if the environment is OK so that the safeplan agent can operate"""
    return try_connect("https://safeplan.at") or try_connect("https://google.at")

def is_initialized():
    """Returns if the device is initialized by checking the .safeplan folder"""
    return False

def try_connect(url):
    """Retruns true if the connect was successful"""
    try:
        requests.get(url)
        return True
    except requests.exceptions.RequestException:
        LOGGER.error("Failed to connect to %s", url)
        return False

if __name__ == '__main__':
    print(is_online())
