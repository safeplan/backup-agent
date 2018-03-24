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
last_modified = None
MAX_AGE_SECONDS= 12 * 3600


def do_work():
    """Background worker"""
    LOGGER.info("starting worker.")

    global offsite_archive_process
    global offsite_archive_process_started
    global last_modified

    device_details = safeplan_server.device_api.device_get_details(environment.get_safeplan_id())

    if not device_details.status in ['in_operation', 'initialized']:
        LOGGER.error("Device's status is '{}'. Aborting.".format(device_details.status))
        return
      
    offsite_archive_process_just_finished = False

    if offsite_archive_process != None:
        rc = offsite_archive_process.poll()
        if rc is None:
            LOGGER.info('offsite archive process running since %s, pid %d', offsite_archive_process_started.strftime("%Y-%m-%dT%H:%M:%S"),offsite_archive_process.pid)
        else:
            offsite_archive_process = None
            offsite_archive_process_just_finished = True
    
    if not offsite_archive_process:
        current_timestamp = datetime.now()

        if offsite_archive_process_just_finished or not last_modified:
            last_modified = fetch_offsite_status()

        if environment.get_forced_mode():
            action = environment.get_forced_mode()
            environment.set_forced_mode(None)
        else:
            if not last_modified:
                action = 'backup'
            elif environment.get_current_mode() == 'backup' and (datetime.now() - last_modified).seconds > MAX_AGE_SECONDS:
                action = 'backup'
            else:
                action = 'idle'


        LOGGER.info("worker is in mode {}".format(action))

        if action == 'backup':
            try:                
                LOGGER.info("Starting offsite backup")
                borg_commands.break_lock(borg_commands.REMOTE_REPO)
                offsite_archive_process = borg_commands.create_archive(borg_commands.REMOTE_REPO,"offsite_" + current_timestamp.strftime("%Y-%m-%dT%H:%M:%S")) 
                offsite_archive_process_started = datetime.now()
                LOGGER.info("Backup process has pid {}".format(offsite_archive_process.pid))

            except Exception as ex:
                LOGGER.error('failed to start offsite backup process')
                LOGGER.exception(ex)
            

    ip_address = environment.get_ip_address()
     
    safeplan_server.device_api.device_update_status(
        environment.get_safeplan_id(),
        DeviceStatus(ip_address = ip_address))


    LOGGER.info("worker finished.")


def get_last_modified(repo_info, repo_list):

    if repo_list and ('archives' in repo_list) and repo_list['archives'][-1]['archive'].endswith(".checkpoint"):
        return None
    try:
        return dateutil.parser.parse(repo_info['repository']['last_modified'])
    except:
        return None


def fetch_offsite_status():
    try:

        repo_info = borg_commands.get_info(borg_commands.REMOTE_REPO)
        repo_list = borg_commands.get_list(borg_commands.REMOTE_REPO)

        with open("{}/offsite-info.json".format(environment.PATH_WORK), 'w') as outfile:
            json.dump(repo_info, outfile)

        with open("{}/offsite-list.json".format(environment.PATH_WORK), 'w') as outfile:
            json.dump(repo_list,outfile)

        last_modified = get_last_modified(repo_info,repo_list)

        age = int((datetime.now() - last_modified).seconds / 3600) if last_modified else -1

        if age >= 0:
            description = "Repository last modified at {}. As of {} it's {} hour(s) old".format(last_modified.strftime("%Y-%m-%d %H:%M:%S"),datetime.now().strftime("%Y-%m-%d %H:%M:%S"), age)
        else:
            description = "A complete backup process has not yet completed"
    
        LOGGER.info(description)

        if environment.get_cc_api_key():
            method = "ok" if age >= 0 and age < 24 else "fail"
            url = "https://secure.armstrongconsulting.com/cc/api/agent/SAFEPLAN_{}/{}?parentApiKey={}".format(environment.get_safeplan_id(),method,environment.get_cc_api_key())  
            try:
                requests.post(url=url, data= description)
            except Exception as ex1: 
                LOGGER.error('Failed to report to control center')
                LOGGER.exception(ex1)    

        return  last_modified
    except Exception as ex:
        LOGGER.error('failed to retrieve status of offsite repository')
        LOGGER.exception(ex)

def get_current_offsite_process():
    global offsite_archive_process
    global offsite_archive_process_started

    return offsite_archive_process, offsite_archive_process_started