"""Initializing operations"""

import logging
import subprocess
import environment
import json
from datetime import datetime

LOGGER = logging.getLogger()
#LOCAL_REPO = "{}/backup".format(environment.PATH_LOCAL_REPO)
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

    LOGGER.info(cmd)
    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait(timeout=30)

    out, err = process.communicate()

    if out:
        LOGGER.info(out.decode("utf-8"))
    if err:
        LOGGER.info(err.decode("utf-8"))

    if process.returncode in [0, 2]:  # An already initialized repository will return 2
        return True
    else:
        raise ValueError("Unexpected return code from borg while initializing the local repo")


def get_info(repo):
    """
    Get's the repo's info from the repository
    """
    cmd = "borg info \
        --json \
        {}".format(repo)

    LOGGER.info(cmd)
    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait(timeout=30)

    out, err = process.communicate()

    if err:
        LOGGER.error("Failed to get status from repo %s. %s", repo, err.decode("utf-8"))
    return json.loads(out.decode("utf-8"))


def get_list(repo):
    """
    Lists the  repository
    """
    cmd = "borg list --last 10 \
        --json \
        {}".format(repo)

    LOGGER.info(cmd)
    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait(timeout=30)

    out, err = process.communicate()

    if err:
        LOGGER.error("Failed to get status from repo %s. %s", repo, err.decode("utf-8"))
    return json.loads(out.decode("utf-8"))


def break_lock(repo):
    """
    Lists the  repository
    """
    cmd = "borg break-lock {}".format(repo)

    LOGGER.info(cmd)
    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait(timeout=30)

    out, err = process.communicate()

    if err:
        LOGGER.error("Failed to break lock for repo %s. %s", repo, err.decode("utf-8"))

    if out:
        LOGGER.info(out.decode("utf-8"))


def create_archive(repo, archive_name):
    """
    Creates an archive
    """

    cmd = "borg create --remote-ratelimit 2097152 --list --stats --show-version --show-rc {repo}::{archive_name} {backup_path} > {log_dir}/backup_{archive_name}.log 2>&1 </dev/null".format(
        repo=repo,
        archive_name=archive_name,
        backup_path=environment.PATH_BACKUP,
        log_dir=environment.PATH_WORK)

    LOGGER.info(cmd)
    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process


def prune(repo):
    """
    Prunes an archive
    """

    cmd = "borg prune -v --list --show-rc --keep-daily=90 --keep-weekly=52 --keep-monthly=84 --keep-yearly=30 {repo} > {log_dir}/backup_prune.log 2>&1 </dev/null".format(
        repo=repo,
        log_dir=environment.PATH_WORK)
    LOGGER.info(cmd)
    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process


def mount(repo):
    """
    Mounts the local archive
    """
    cmd = "while true; do borg mount --debug --foreground --strip-components 3 -o nonempty,allow_other {repo} {mount_point} >> {log_file_path} 2>&1 </dev/null; if [[ $? == 0 ]]; then break; fi; sleep 5; borg umount {mount_point}; done".format(
        repo=repo,
        mount_point=environment.PATH_MOUNTPOINT,
        log_file_path="{}/mount.log".format(environment.PATH_WORK))
    LOGGER.info(cmd)
    process = subprocess.Popen(cmd, shell=True, executable="/bin/bash", stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process


def unmount():
    """
    Unmounts the local archive
    """

    cmd = "borg umount {}".format(environment.PATH_MOUNTPOINT)
    LOGGER.info(cmd)
    process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait(timeout=30)
    out, err = process.communicate()

    if out:
        LOGGER.info(out.decode("utf-8"))
    if err:
        LOGGER.info(err.decode("utf-8"))
