"""Safeplan environment"""
import os
import logging
import requests

LOGGER = logging.getLogger()

PATH_BACKUP = "/var/safeplan/backup"
PATH_CONFIG = "/var/safeplan/config"
PATH_LOCAL_REPO = "/var/safeplan/repo"
PATH_WORK = "/var/safeplan/work"

FILENAME_BORG_PASSPHRASE = "/var/safeplan/config/borg_passphrase"
FILENAME_PRIVATE_KEY = os.path.join(PATH_CONFIG, "id_rsa")
FILENAME_PUBLIC_KEY = os.path.join(PATH_CONFIG, "id_rsa.pub")

SAFEPLAN_SSH = "safeplan-device@backup.safeplan.at:2222"

def is_online():
    """Checks if the environment is OK so that the safeplan agent can operate"""
    return try_connect("https://safeplan.at") or try_connect("https://google.at")

def try_connect(url):
    """Retruns true if the connect was successful"""
    try:
        requests.get(url)
        return True
    except requests.exceptions.RequestException:
        LOGGER.error("Failed to connect to %s", url)
        return False

def get_ip_address():
   """
   Returns the IP address provided by the HOST_IP Environment variable

   on a safeplan device, set it as follows
   HOST_ID = $(ip -4 addr show eth0| grep -Po 'inet \K[\d.]+')
   """

   return os.environ['HOST_IP']

def get_safeplan_id():
    """
    Returns the assigned safeplan id
    """
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