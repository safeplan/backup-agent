"""Initializing operations"""

import logging
import subprocess
import environment
import json

LOGGER = logging.getLogger("borg")
LOCAL_REPO = "{}/backup".format(environment.PATH_LOCAL_REPO)
REMOTE_REPO = "ssh://{}/repos/{}/backup".format(
    environment.SAFEPLAN_SSH,
    environment.get_safeplan_id())

def init(repo):
    """
    Initializes the local repository
    """

    cmd = "borg init \
        --encryption=repokey \
        {}".format(repo)

    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait(timeout=30)
    
    out, err = process.communicate()
    
    if out:
        LOGGER.info(out.decode("utf-8"))
    if err:
        LOGGER.info(err.decode("utf-8"))
    
    if process.returncode in [0,2]: #An already initialized repository will return 2
        return True
    else:
        raise ValueError("Unexpected return code from borg while initializing the local repo")
 
def get_info(repo):
    """
    Initializes the local repository
    """
    cmd = "borg info \
        --json \
        {}".format(repo)

    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait(timeout=30)

    out, err = process.communicate()

    if err:
        LOGGER.error("Failed to get status from local repo. %s", err.decode("utf-8"))        
    return json.loads(out.decode("utf-8"))

def create_archive(repo):
    """
    Creates an archive
    """
    #borg create /path/to/repo::{hostname}-{user}-{now:%Y-%m-%dT%H:%M:%S.%f} ~