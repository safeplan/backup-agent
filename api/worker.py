"""Initializing operations"""

import logging
import environment
from  safeplan_server import device_api
from safeplan.models import DeviceStatus
import os
from datetime import datetime
import borg_commands
import json
import dateutil
import requests

LOGGER = logging.getLogger()

mount_process = None
offsite_archive_process = None
offsite_archive_process_started = None
last_backup_timestamp = None
last_modified = None
last_pruned = None
MAX_AGE_SECONDS= 12 * 3600

is_allowed_to_remount = False


def do_work():
    """Background worker"""
    LOGGER.info("starting worker.")

    global is_allowed_to_remount 
    global mount_process
    global offsite_archive_process
    global offsite_archive_process_started
    global last_backup_timestamp
    global last_modified
    global last_pruned

    touch_backup()

    is_allowed_to_remount = False
    device_details = device_api.device_get_details(environment.get_safeplan_id())
    executed_operation = 'noop'
    if not device_details.status in ['in_operation', 'initialized']:
        LOGGER.error("Device's status is '{}'. Aborting.".format(device_details.status))
        return executed_operation
      
    offsite_archive_process_just_finished = False

    if offsite_archive_process != None:
        rc = offsite_archive_process.poll()
        if rc is None:
            LOGGER.info('offsite archive process running since %s, pid %d', offsite_archive_process_started.strftime("%Y-%m-%dT%H:%M:%S"),offsite_archive_process.pid)
        else:
            offsite_archive_process = None
            offsite_archive_process_just_finished = True

    if mount_process !=  None:
        rc = mount_process.poll()
        if rc is None:
            LOGGER.info('offsite mount process {} is active'.format(mount_process.pid))
        else:
            mount_process = None
 
    if not offsite_archive_process:
        current_timestamp = datetime.now()

        if offsite_archive_process_just_finished or not last_backup_timestamp:
            last_backup_timestamp, last_modified, last_pruned = fetch_offsite_status()
            executed_operation = 'fetched_status'

        if environment.get_forced_mode():
            action = environment.get_forced_mode()
            environment.set_forced_mode(None)
        else:
            if not last_backup_timestamp:
                action = 'backup'
            elif environment.get_current_mode() == 'backup' and (datetime.now() - last_backup_timestamp).total_seconds() > MAX_AGE_SECONDS:
                action = 'backup'
            elif environment.get_current_mode() == 'cleanup' and (last_pruned == None or (datetime.now() - last_pruned).total_seconds() > MAX_AGE_SECONDS):
                action = 'prune'
            else:
                action = 'idle'


        LOGGER.info("worker is in {} mode. last backup completed: {}; last modified: {}; last pruned: {}".format(action,strdatetime(last_backup_timestamp),strdatetime(last_modified),strdatetime(last_pruned)))

        if action != 'idle':
            unmount()

        if action == 'backup':
            try:                
                LOGGER.info("Starting offsite backup")
                borg_commands.break_lock(borg_commands.REMOTE_REPO)
                offsite_archive_process = borg_commands.create_archive(borg_commands.REMOTE_REPO,"offsite_" + current_timestamp.strftime("%Y-%m-%dT%H:%M:%S")) 
                offsite_archive_process_started = datetime.now()
                LOGGER.info("Backup process has pid {}".format(offsite_archive_process.pid))
                executed_operation = 'started_backup'

            except Exception as ex:
                LOGGER.error('failed to start offsite backup process')
                LOGGER.exception(ex)
        elif action == 'prune':
            try:                
                LOGGER.info("Starting to prune repository")
                borg_commands.break_lock(borg_commands.REMOTE_REPO)
                offsite_archive_process = borg_commands.prune(borg_commands.REMOTE_REPO)
                offsite_archive_process_started = datetime.now()
                LOGGER.info("Prune process has pid {}".format(offsite_archive_process.pid))
                executed_operation = 'started_prune'
            except Exception as ex:
                LOGGER.error('failed to start offsite backup process')
                LOGGER.exception(ex)
        elif action == 'idle':
            if not mount_process:
                mount(True)
                executed_operation = 'mount'
            is_allowed_to_remount = True
    else:
        action = "backup"

    ip_address = environment.get_ip_address()
     
    device_api.device_update_status(
        environment.get_safeplan_id(),
        DeviceStatus(
            ip_address = ip_address,
            last_backup=last_backup_timestamp,
            last_pruned=last_pruned,
            last_action=action,
            last_action_as_of=datetime.utcnow()
        ))


    LOGGER.info("worker finished. Executed operation: {}".format(executed_operation))
    return executed_operation


def get_last_backed_up (repo_list):
    if repo_list and ('archives' in repo_list) and len(repo_list['archives']) > 0:
        most_recent = repo_list['archives'][-1]
        if most_recent['archive'].endswith(".checkpoint"):
            return None
        else:
            return dateutil.parser.parse(most_recent['time'])
    else:
        return None

def fetch_offsite_status():
    try:

        borg_commands.break_lock(borg_commands.REMOTE_REPO)
        repo_info = borg_commands.get_info(borg_commands.REMOTE_REPO)
        repo_list = borg_commands.get_list(borg_commands.REMOTE_REPO)

        with open("{}/offsite-info.json".format(environment.PATH_WORK), 'w') as outfile:
            json.dump(repo_info, outfile)

        with open("{}/offsite-list.json".format(environment.PATH_WORK), 'w') as outfile:
            json.dump(repo_list,outfile)

        last_pruned = None
        prune_logfile = "{}/backup_prune.log".format(environment.PATH_WORK)
        if os.path.exists(prune_logfile):
            with open(prune_logfile, 'r') as f:
                if 'terminating with success' in f.read():
                  last_pruned =  datetime.fromtimestamp(os.path.getmtime(prune_logfile))

        last_backup_timestamp = get_last_backed_up(repo_list)
        last_modified = None
        try:
            last_modified = dateutil.parser.parse(repo_info['repository']['last_modified'])
        except:
            pass

        age = int((datetime.now() - last_backup_timestamp).total_seconds() / 3600) if last_backup_timestamp else -1

        if age >= 0:
            description = "Last offsite backup occurred at {}. As of {} it's {} hour(s) old. Last pruned: {}".format(strdatetime(last_backup_timestamp),strdatetime(datetime.now()), age, strdatetime(last_pruned))
        else:
            description = "A complete backup process has not yet completed"
    
        LOGGER.info("Repository status has been updated. %s",description)

        if environment.get_cc_api_key():
            method = "ok" if age >= 0 and age < 24 else "fail"
            url = "https://secure.armstrongconsulting.com/cc/api/agent/SAFEPLAN_{}/{}?parentApiKey={}".format(environment.get_safeplan_id(),method,environment.get_cc_api_key())  
            try:
                requests.post(url=url, data= description)
            except Exception as ex1: 
                LOGGER.error('Failed to report to control center')
                LOGGER.exception(ex1)    

        return  last_backup_timestamp, last_modified, last_pruned
    except Exception as ex:
        LOGGER.error('failed to retrieve status of offsite repository')
        LOGGER.exception(ex)

def get_current_offsite_process():
    global offsite_archive_process
    global offsite_archive_process_started

    return offsite_archive_process, offsite_archive_process_started

def strdatetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""

def unmount():
    global mount_process
    if mount_process != None:
        LOGGER.info("Unmounting mount process {}".format(mount_process.pid))

    borg_commands.unmount()
    mount_process = None

    if(os.path.exists(environment.PATH_MOUNTPOINT)):
        os.rmdir(environment.PATH_MOUNTPOINT)


def mount(forced=False):
    global mount_process

    if not forced and not is_allowed_to_remount:
        LOGGER.info("Currently not allowed to mount...")
        return

    #If there is a running mount_process, exit
    if mount_process and mount_process.poll() == None:
        LOGGER.info("Offsite archive already mounted by process {}".format(mount_process.pid))
        return

    try:
        unmount()
        LOGGER.info("Now mounting offsite archive")
        if not os.path.exists(environment.PATH_MOUNTPOINT):
            os.makedirs(environment.PATH_MOUNTPOINT, 0o700)
        mount_process = borg_commands.mount(borg_commands.REMOTE_REPO)
        LOGGER.info("Offsite archive mounted by process {}".format(mount_process.pid))
        
    except Exception as ex:
        LOGGER.error('failed to mount offsite archive')
        LOGGER.exception(ex)

def touch_backup():
    try:
        touch_file = os.path.join(environment.PATH_BACKUP, ".safeplan-modified")
        with open(touch_file, mode='w') as file:
            file.write(strdatetime(datetime.now()))
    except Exception as ex:
        LOGGER.error('failed to write to {}'.format(touch_file))
        LOGGER.exception(ex)
