"""Initializing operations"""

import logging
import environment
import safeplan_server
from safeplan.models import DeviceStatus
import os
from datetime import datetime
import borg_commands
import json
import dateutil
import requests

LOGGER = logging.getLogger()

offsite_archive_process = None
offsite_archive_process_started = None
offsite_archive_process_check = None


MAX_AGE_HOURS = 12
TRY_BACKUP_EVERY_MINUTES=30

def get_current_offsite_process():
    global offsite_archive_process
    global offsite_archive_process_started

    return offsite_archive_process, offsite_archive_process_started

def do_work():
    """Background worker"""
    LOGGER.info("starting worker.")

    global offsite_archive_process_check
    global MAX_AGE_HOURS
    global offsite_archive_process
    global TRY_BACKUP_EVERY_MINUTES
    global offsite_archive_process_started
   
    
    device_details = safeplan_server.device_api.device_get_details(environment.get_safeplan_id())

    if not device_details.status in ['in_operation', 'initialized']:
        LOGGER.error("Device's status is '{}'. Aborting.".format(device_details.status))
        return

    current_timestamp = datetime.now()
 
    # Check the offsite archive process's status
    offsite_archive_process_just_finished = False

    if offsite_archive_process != None:
        rc = offsite_archive_process.poll()
        if rc is None:
            LOGGER.info('offsite archive process running since %s, pid %d', offsite_archive_process_started.strftime("%Y-%m-%dT%H:%M:%S"),offsite_archive_process.pid)
        else:
            offsite_archive_process = None
            offsite_archive_process_just_finished = True

    current_mode = environment.get_current_mode()
    archive_process_is_active = offsite_archive_process != None
    forced = False

    #if the current mode is 'backup' and 'idle' is requested manually switch mode.
    if environment.get_forced_mode() == 'backup':
        if (current_mode == 'backup'):
            # backup is requested, however we are in backup mode -> reset forced mode
            environment.set_forced_mode(None)
        else:    
            if (current_mode == 'idle'):
                if archive_process_is_active:
                    LOGGER.info("Switching into 'backup' has been requested. Waiting until the currently running archive process terminate.")
                else:
                    forced = True
                    current_mode = 'backup'
                    LOGGER.info("Forcing current_mode from 'idle' to 'backup'")
                    environment.set_forced_mode(None)
                   

    if environment.get_forced_mode() == 'idle':
        if (current_mode == 'idle'):
            # idle is requested, however we are in idle mode -> reset forced mode
            environment.set_forced_mode(None)
        else:    
            if (current_mode == 'backup'):
                if archive_process_is_active:
                    LOGGER.info("Switching into 'idle' has been requested. Waiting until the currently running archive process terminate.")
                else:
                    current_mode = 'backup'
                    LOGGER.info("Forcing current_mode from 'backup' to 'idle'")
                    forced = True
                    environment.set_forced_mode(None)


    LOGGER.info("Current mode is {}".format(current_mode))

    if offsite_archive_process_just_finished:
        fetch_offsite_status()

    if current_mode == 'backup':

        do_offsite_backup =False
        if offsite_archive_process == None:
            if forced or get_minutes_since_last_offsite_archive() > TRY_BACKUP_EVERY_MINUTES:
                try:                
                    #Init the repo (if it does not already exist)
                    borg_commands.init(borg_commands.REMOTE_REPO)
                    borg_commands.break_lock(borg_commands.REMOTE_REPO)

                    age = fetch_offsite_status()

                    if forced:
                        do_offsite_backup = True
                    else:
                        LOGGER.info("offsite backup is {} hours old".format(age))
                        do_offsite_backup = age > MAX_AGE_HOURS

                    offsite_archive_process_check = datetime.now()
 
                except Exception as ex:
                    LOGGER.error('failed to retrieve status of offsite repository')
                    LOGGER.exception(ex)
            else:
                LOGGER.info('Last offsite backup attempt is {} minutes ago. Will try again later'.format(get_minutes_since_last_offsite_archive()))
                

        if do_offsite_backup:
            LOGGER.info("Starting offsite backup")
            offsite_archive_process = borg_commands.create_archive(borg_commands.REMOTE_REPO,"offsite_" + current_timestamp.strftime("%Y-%m-%dT%H:%M:%S")) 
            offsite_archive_process_started = datetime.now()
        else:
            LOGGER.info("No need to start another offsite backup")
            
    ip_address = environment.get_ip_address()
     
    safeplan_server.device_api.device_update_status(
        environment.get_safeplan_id(),
        DeviceStatus(ip_address = ip_address))


    LOGGER.info("worker finished.")


def get_age_in_hours(repo_info):
    try:
        return int((datetime.now() - dateutil.parser.parse(repo_info['repository']['last_modified'])).seconds / 3600)
    except:
        return 99

def get_minutes_since_last_offsite_archive():
    global offsite_archive_process_check
    
    if not offsite_archive_process_check:
        return 999

    return int((datetime.now() - offsite_archive_process_check).seconds / 60)


def fetch_offsite_status():
    try:
        repo_info = borg_commands.get_info(borg_commands.REMOTE_REPO)
        LOGGER.info("offsite Repository is ok, last modified: %s",
                    repo_info['repository']['last_modified'])

        repo_list = borg_commands.get_list(borg_commands.REMOTE_REPO)

        with open("{}/offsite-info.json".format(environment.PATH_WORK), 'w') as outfile:
            json.dump(repo_info, outfile)

        with open("{}/offsite-list.json".format(environment.PATH_WORK), 'w') as outfile:
            json.dump(repo_list, outfile)

        age = get_age_in_hours(repo_info)

        if environment.get_cc_api_key():
            method = "ok" if age < 24 else "fail"
            url = "https://secure.armstrongconsulting.com/cc/api/agent/SAFEPLAN_{}/{}?parentApiKey={}".format(environment.get_safeplan_id(),method,environment.get_cc_api_key())  
            try:
                data = "As of {}, repository is {} hour(s) old".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), age)
                requests.post(url=url, data= data)
                LOGGER.info("Submitted '{}' to control center".format(data))
            except Exception as ex1: 
                LOGGER.error('Failed to report to control center')
                LOGGER.exception(ex1)    

        return  age
    except Exception as ex:
        LOGGER.error('failed to retrieve status of offsite repository')
        LOGGER.exception(ex)
        