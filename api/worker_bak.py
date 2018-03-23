"""Initializing operations"""

import logging
import environment
from safeplan.apis import DeviceApi
from safeplan.models import DeviceStatus
import os
from datetime import datetime
import borg_commands
import json
import dateutil

LOGGER = logging.getLogger()
SAFEPLAN = DeviceApi()

#onsite_archive_process = None
offsite_archive_process = None

#onsite_archive_process_started  = None
offsite_archive_process_started = None

#mount_process = None
MAX_AGE_HOURS = 12

def do_work():
    """Background worker"""
    LOGGER.info("starting worker.")

    global MAX_AGE_HOURS
#    global onsite_archive_process
    global offsite_archive_process

#    global onsite_archive_process_started
    global offsite_archive_process_started
    
#    global mount_process

    current_timestamp = format_utc_time(datetime.utcnow())
 
#    # Check the onsite archive process's status
#    if onsite_archive_process != None:
#        rc = onsite_archive_process.poll()
#        if rc is None:
#            LOGGER.info('onsite archive process running since %s, pid %d', format_utc_time(onsite_archive_process_started),onsite_archive_process.pid)
#        else:
#            onsite_archive_process = None

    # Check the offsite archive process's status

    offsite_archive_process_just_finished = False

    if offsite_archive_process != None:
        rc = offsite_archive_process.poll()
        if rc is None:
            LOGGER.info('offsite archive process running since %s, pid %d', format_utc_time(offsite_archive_process_started),offsite_archive_process.pid)
        else:
            offsite_archive_process = None
            offsite_archive_process_just_finished = True

    current_mode = environment.get_current_mode()

#    archive_process_is_active = onsite_archive_process != None or offsite_archive_process != None
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
                    current_mode = 'backup'
                    LOGGER.info("Forcing current_mode from 'idle' to 'backup'")
                    forced = True

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


    LOGGER.info("Current mode is {}".format(current_mode))


    if offsite_archive_process_just_finished:
        fetch_offsite_status()


#    if current_mode == 'idle':
#        if mount_process != None:
#            rc = mount_process.poll()
#            if rc is None:
#                do_mount = False # Already mounted.
#            else:
#                do_mount = True
#        else:
#            do_mount = True
#
#        if do_mount:
#           if onsite_archive_process:
#                LOGGER.info("Though in 'idle' mode, there is currently an onsite archive  process running; mounting will be done after this has been finished")
#           else:    
#                borg_commands.unmount() #If a previous mount was interrupted, this will clean-up
#                mount_process = borg_commands.mount() 
#                LOGGER.info('Mounted onsite archive, pid = %d',mount_process.pid)        
#                environment.set_forced_mode(None)
#        else:
#            LOGGER.info('onsite archive is already mounted. Nothing todo.')

        
    if current_mode == 'backup':

#        do_onsite_backup = False
        do_offsite_backup =False
     
        mount_process = None

#        if onsite_archive_process == None:
#            try:
#
#                #Blindly unmount...    
#               borg_commands.unmount()
#
#                #Init the repo (if it does not already exist)
#                borg_commands.init(borg_commands.LOCAL_REPO)
#                borg_commands.break_lock(borg_commands.LOCAL_REPO)
#
#                repo_info = borg_commands.get_info(borg_commands.LOCAL_REPO)
#                LOGGER.info("onsite Repository is ok, last modified: %s",
#                            repo_info['repository']['last_modified'])
#
#                repo_list = borg_commands.get_list(borg_commands.LOCAL_REPO)
#
#                with open("{}/onsite-info.json".format(environment.PATH_WORK), 'w') as outfile:
#                    json.dump(repo_info, outfile)
#
#                with open("{}/onsite-list.json".format(environment.PATH_WORK), 'w') as outfile:
#                    json.dump(repo_list, outfile)
#
#                if forced:
#                    do_onsite_backup = True
#                else:
#                    age = get_age_in_hours(repo_info)
#                    LOGGER.info("onsite backup is {} hours old".format(age))
#                    do_onsite_backup = age > MAX_AGE_HOURS
#
#            except Exception as ex:
#                LOGGER.error('failed to retrieve status of onsite repository')
#                LOGGER.exception(ex)

        if offsite_archive_process == None:
            try:
                
                #Init the repo (if it does not already exist)
                borg_commands.init(borg_commands.REMOTE_REPO)
                borg_commands.break_lock(borg_commands.REMOTE_REPO)

                fetch_offsite_status()

                if forced:
                    do_offsite_backup = True
                else:
                    age = get_age_in_hours(repo_info)
                    LOGGER.info("offsite backup is {} hours old".format(age))
                    do_offsite_backup = age > MAX_AGE_HOURS

            except Exception as ex:
                LOGGER.error('failed to retrieve status of offsite repository')
                LOGGER.exception(ex)


#        if do_onsite_backup:
#            LOGGER.info("Starting onsite backup")
#            onsite_archive_process = borg_commands.create_archive(borg_commands.LOCAL_REPO,"onsite_" + current_timestamp) 
#            onsite_archive_process_started = datetime.utcnow()
#            environment.set_forced_mode(None)
#        else:
#            LOGGER.info("No need to start another onsite backup")

        if do_offsite_backup:
            LOGGER.info("Starting offsite backup")
            offsite_archive_process = borg_commands.create_archive(borg_commands.REMOTE_REPO,"offsite_" + current_timestamp) 
            offsite_archive_process_started = datetime.utcnow()
            environment.set_forced_mode(None)
        else:
            LOGGER.info("No need to start another offsite backup")
  

    ip_address = environment.get_ip_address()
     
    SAFEPLAN.device_update_status(
        environment.get_safeplan_id(),
        DeviceStatus(ip_address = ip_address))

    

    LOGGER.info("worker finished.")
    
def format_utc_time(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")

def get_age_in_hours(repo_info):
    try:
        return int((datetime.now() - dateutil.parser.parse(repo_info['repository']['last_modified'])).seconds / 3600)
    except:
        return 99

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

    except Exception as ex:
        LOGGER.error('failed to retrieve status of offsite repository')
        LOGGER.exception(ex)
        