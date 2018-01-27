"""Initializing operations"""

import logging
import os
from random import choice
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import environment
from safeplan.apis import DeviceApi
from safeplan.models import InitializationInformation
import borg_commands

LOGGER = logging.getLogger("initializer")


SAFEPLAN = DeviceApi()

def has_rsa_keys():
    """
    Checks if the rsa keys exist
    """
    return os.path.exists(environment.FILENAME_PRIVATE_KEY)

def has_borg_passphrase():
    """
    Checks if the passphrase has been created
    """
    return os.path.exists(environment.FILENAME_BORG_PASSPHRASE)

def create_borg_passphrase():
    """
    Creates and stores a new borg passphrase
    """
    if not os.path.exists(environment.PATH_CONFIG):
        LOGGER.warning("Creating config path %s", environment.PATH_CONFIG)
        os.makedirs(environment.PATH_CONFIG, 0o700)

    if not has_borg_passphrase():
        LOGGER.warning("Creating new borg passphrase")  
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890"
        passphrase = ''.join(choice(chars) for _ in range(1024))

        with open(environment.FILENAME_BORG_PASSPHRASE, mode='w') as file:
            file.write(passphrase)

        os.chmod(environment.FILENAME_BORG_PASSPHRASE, 0o444)

def create_rsa_keys():
    """Initializes the backup-agent"""

    if not os.path.exists(environment.PATH_CONFIG):
        LOGGER.warning("Creating config path %s", environment.PATH_CONFIG)
        os.makedirs(environment.PATH_CONFIG, 0o700)

    if not has_rsa_keys():
        LOGGER.warning("creating new rsa keys")
        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=2048)

        # get public key in OpenSSH format
        public_key = key.public_key().public_bytes(serialization.Encoding.OpenSSH, \
            serialization.PublicFormat.OpenSSH)

        # get private key in PEM container format
        pem = key.private_bytes(encoding=serialization.Encoding.PEM,
                                format=serialization.PrivateFormat.TraditionalOpenSSL,
                                encryption_algorithm=serialization.NoEncryption())

        # decode to printable strings
        private_key_str = pem.decode('utf-8')
        public_key_str = public_key.decode('utf-8')

        with open(environment.FILENAME_PRIVATE_KEY, mode='w') as file:
            file.write(private_key_str)

        with open(environment.FILENAME_PUBLIC_KEY, mode='w') as file:
            file.write(public_key_str)

        os.chmod(environment.FILENAME_PUBLIC_KEY, 0o444)
        os.chmod(environment.FILENAME_PUBLIC_KEY, 0o400)
    else:
        LOGGER.info("RSA keys have already been created, reusing existing RSA keys")

def initialize():
    """
    Initializes the device with the device
    """

    if not has_rsa_keys():
        create_rsa_keys()

    if not has_borg_passphrase():
        create_borg_passphrase()


    if not os.path.exists("{}/backup".format(environment.PATH_LOCAL_REPO)):
        LOGGER.warning("Creating local repository")
        os.makedirs("{}/backup".format(environment.PATH_LOCAL_REPO), 0o700)


    LOGGER.info("submitting public key to safeplan server")
    SAFEPLAN.device_initialize(environment.get_safeplan_id(),
                             InitializationInformation(rsa_public_key=environment.get_rsa_public_key()))

    os.environ['BORG_CACHE_DIR'] = environment.PATH_WORK    
    os.environ['BORG_BASE_DIR'] = environment.PATH_CONFIG
    os.environ['BORG_PASSPHRASE'] = environment.get_borg_passphrase()
    os.environ['BORG_RELOCATED_REPO_ACCESS_IS_OK'] = 'YES'

    borg_commands.init(borg_commands.LOCAL_REPO)
    borg_commands.init(borg_commands.REMOTE_REPO)

    LOGGER.info("Local Repository is ok, last modified: %s",
                borg_commands.get_info(borg_commands.LOCAL_REPO)['repository']['last_modified'])
  
    LOGGER.info("Remote Repository is ok, last modified: %s",
                borg_commands.get_info(borg_commands.REMOTE_REPO)['repository']['last_modified'])
  
    LOGGER.info("initialized ok.")
    