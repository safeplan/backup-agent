"""Initializing operations"""

import logging
import os
from random import choice
import environment
from safeplan.models import InitializationInformation
import borg_commands
import socket
import getpass
import subprocess
import worker
import safeplan_server
import cc

LOGGER = logging.getLogger()


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

        process = subprocess.Popen("ssh-keygen -f {}/id_rsa -t rsa -N ''".format(environment.get_ssh_key_path()), shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait(timeout=30)

        out, err = process.communicate()

        if out:
            LOGGER.error(out.decode("utf-8"))

        if err:
            LOGGER.info(err.decode("utf-8"))

        if not process.returncode in [0]:
            raise ValueError("Unexpected return code from ssh-keygen")

        with open("{}/config".format(environment.get_ssh_key_path()), mode='w') as file:
            file.writelines("Host *\n   StrictHostKeyChecking no")

    else:
        LOGGER.info("RSA keys have already been created, reusing existing RSA keys")


def self_check():
    errors = []
    if not os.path.exists(environment.PATH_WORK):
        errors.append("work directory {} does not exist".format(environment.PATH_WORK))
    if not os.path.exists(environment.PATH_CONFIG):
        errors.append("config directory {} does not exist".format(environment.PATH_CONFIG))
    if not os.path.exists(environment.PATH_BACKUP):
        errors.append("backup directory {} does not exist".format(environment.PATH_BACKUP))
    if not errors:
        cc.report_to_control_center("incident", "self check passed")
        return True
    else:
        cc.report_to_control_center("fail", "self check failed: {}".format(errors))
        return False


def initialize():
    """
    Initializes the device
    """

    # read the build number from file - its updated by the build.sh script
    build_number = "?"
    with open("__buildnumber.txt", "r") as bfile:
        build_number = bfile.read()
    cc.report_to_control_center("incident", "backup-agent version {} starting up - initializing device".format(build_number))

    if not self_check():
        return

    if not has_rsa_keys():
        create_rsa_keys()

    if not has_borg_passphrase():
        cc.report_to_control_center("incident", "creating new borg passphrase")
        create_borg_passphrase()

    LOGGER.info("submitting public key to safeplan server")
    safeplan_server.device_api.device_initialize(environment.get_safeplan_id(), InitializationInformation(rsa_public_key=environment.get_rsa_public_key()))

    os.environ['BORG_CACHE_DIR'] = environment.PATH_WORK
    os.environ['BORG_BASE_DIR'] = environment.PATH_CONFIG
    os.environ['BORG_PASSPHRASE'] = environment.get_borg_passphrase()
    os.environ['BORG_RELOCATED_REPO_ACCESS_IS_OK'] = 'YES'

    LOGGER.info("BORG_CACHE_DIR is {}".format(os.environ['BORG_CACHE_DIR']))
    LOGGER.info("BORG_BASE_DIR is {}".format(os.environ['BORG_CACHE_DIR']))
    LOGGER.info("BORG_PASSPHRASE length is {}".format(len(os.environ['BORG_PASSPHRASE'])))
    LOGGER.info("BORG_RELOCATED_REPO_ACCESS_IS_OK is {}".format(os.environ['BORG_RELOCATED_REPO_ACCESS_IS_OK']))

    borg_commands.init(borg_commands.REMOTE_REPO)

    worker.fetch_offsite_status()

    LOGGER.info("initialized ok.")

    # report an initialization incident to the control-center so we know the device has started up
    cc.report_to_control_center("incident", "device initialized")

    return True
