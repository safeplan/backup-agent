"""Initializing operations"""

import logging
import environment
from safeplan.apis import DeviceApi
from safeplan.models import DeviceStatus
import os
from datetime import datetime
from datetime import timedelta
import borg_commands
import json

LOGGER = logging.getLogger()
SAFEPLAN = DeviceApi()

onsite_archive_process = None
offsite_archive_process = None

onsite_archive_process_started  = None
offsite_archive_process_started = None


def do_work():
    """Background worker"""
    LOGGER.info("starting worker.")

    global onsite_archive_process
    global offsite_archive_process

    global onsite_archive_process_started
    global offsite_archive_process_started
    
    current_timestamp = format_utc_time(datetime.utcnow())
 
    do_onsite_backup = False
    do_offsite_backup=False

    # Check the onsite status
    if onsite_archive_process != None:
        rc = onsite_archive_process.poll()
        if rc is None:
            LOGGER.info('onsite archive process running since %s, pid %d', format_utc_time(onsite_archive_process_started),onsite_archive_process.pid)
        else:
            onsite_archive_process = None
    
    if onsite_archive_process == None:
        try:

            #Init the repo (if it does not already exist)
            borg_commands.init(borg_commands.LOCAL_REPO)
            borg_commands.break_lock(borg_commands.LOCAL_REPO)

            repo_info = borg_commands.get_info(borg_commands.LOCAL_REPO)
            LOGGER.info("onsite Repository is ok, last modified: %s",
                        repo_info['repository']['last_modified'])

            repo_list = borg_commands.get_list(borg_commands.LOCAL_REPO)

            with open("{}/onsite-info.json".format(environment.PATH_WORK), 'w') as outfile:
                json.dump(repo_info, outfile)

            with open("{}/onsite-list.json".format(environment.PATH_WORK), 'w') as outfile:
                json.dump(repo_list, outfile)


            do_onsite_backup = True
        except Exception as ex:
            LOGGER.error('failed to retrieve status of onsite repository')
            LOGGER.exception(ex)


    # Check the offsite status
    if offsite_archive_process != None:
        rc = offsite_archive_process.poll()
        if rc is None:
            LOGGER.info('offsite archive process running since %s, pid %d', format_utc_time(offsite_archive_process_started),offsite_archive_process.pid)
        else:
            offsite_archive_process = None

    if offsite_archive_process == None:
        try:

            #Init the repo (if it does not already exist)
            borg_commands.init(borg_commands.REMOTE_REPO)
            borg_commands.break_lock(borg_commands.REMOTE_REPO)

            repo_info = borg_commands.get_info(borg_commands.REMOTE_REPO)
            LOGGER.info("offsite Repository is ok, last modified: %s",
                        repo_info['repository']['last_modified'])

            repo_list = borg_commands.get_list(borg_commands.REMOTE_REPO)

            with open("{}/offsite-info.json".format(environment.PATH_WORK), 'w') as outfile:
                json.dump(repo_info, outfile)

            with open("{}/offsite-list.json".format(environment.PATH_WORK), 'w') as outfile:
                json.dump(repo_list, outfile)


            do_offsite_backup = True    
        except Exception as ex:
            LOGGER.error('failed to retrieve status of offsite repository')
            LOGGER.exception(ex)


    if do_onsite_backup:
        LOGGER.info("Starting onsite backup")
        onsite_archive_process = borg_commands.create_archive(borg_commands.LOCAL_REPO,"onsite_" + current_timestamp) 
        onsite_archive_process_started = datetime.utcnow();

    if do_offsite_backup:
        LOGGER.info("Starting offsite backup")
        offsite_archive_process = borg_commands.create_archive(borg_commands.REMOTE_REPO,"offsite_" + current_timestamp) 
        offsite_archive_process_started = datetime.utcnow();
  

    ip_address = environment.get_ip_address()
    if ip_address == None:
        LOGGER.error('ipaddress not set (%s)',environment.FILENAME_IP_ADDRESS)
        

    SAFEPLAN.device_update_status(
        environment.get_safeplan_id(),
        DeviceStatus(ip_address = ip_address))

    

    LOGGER.info("worker finished.")
    
def format_utc_time(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")