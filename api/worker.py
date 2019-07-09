import logging
import environment
from safeplan_server import device_api
from safeplan.models import DeviceStatus
import os
from datetime import datetime
import borg_commands
import json
import dateutil
import requests
import subprocess
import cc

LOGGER = logging.getLogger()

mount_process = None
offsite_archive_process = None
offsite_archive_process_started = None
offsite_archive_logfile_name = None
last_backup_timestamp = None
last_modified = None
last_pruned = None
MAX_AGE_SECONDS = 12 * 3600

is_allowed_to_remount = False


def do_work():
    """Background worker"""
    LOGGER.info("starting worker.")

    global is_allowed_to_remount
    global mount_process
    global offsite_archive_process
    global offsite_archive_process_started
    global offsite_archive_logfile_name
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
            LOGGER.info('offsite archive process running since %s, pid %d', offsite_archive_process_started.strftime("%Y-%m-%dT%H:%M:%S"), offsite_archive_process.pid)
        else:
            offsite_archive_process = None
            offsite_archive_process_just_finished = True

    if mount_process != None:
        rc = mount_process.poll()
        if rc is None:
            LOGGER.info('offsite mount process {} is active'.format(mount_process.pid))
        else:
            mount_process = None

    if not offsite_archive_process:
        current_timestamp = datetime.now()

        if offsite_archive_process_just_finished or not last_backup_timestamp:
            last_backup_timestamp, last_modified, last_pruned = fetch_offsite_status()
            if offsite_archive_process_just_finished:  # send the log file summary to control-center
                try:
                    if offsite_archive_logfile_name and os.path.isfile(offsite_archive_logfile_name):
                        with open(offsite_archive_logfile_name, "rt") as log_file:
                            summary = "\n".join(tail(log_file, lines=16))
                            cc.report_to_control_center("incident", "backup log: {}".format(summary))
                except Exception as ex:
                    LOGGER.error('failed to send log file to control center')
                    LOGGER.exception(ex)
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

        LOGGER.info("worker is in {} mode. last backup completed: {}; last modified: {}; last pruned: {}".format(
            action, strdatetime(last_backup_timestamp), strdatetime(last_modified), strdatetime(last_pruned)))

        if action != 'idle':
            unmount()

        if action == 'backup':
            try:
                LOGGER.info("Starting backup")
                borg_commands.break_lock(borg_commands.REMOTE_REPO)
                archive_name = current_timestamp.strftime("%Y_%m_%dT%H_%M_%S")
                offsite_archive_logfile_name = os.path.join(environment.PATH_WORK, "backup_{}.log".format(archive_name))
                offsite_archive_process = borg_commands.create_archive(borg_commands.REMOTE_REPO, archive_name)
                offsite_archive_process_started = datetime.now()
                LOGGER.info("Backup process has pid {}".format(offsite_archive_process.pid))
                cc.report_to_control_center("incident", "backup to archive {} started".format(archive_name))
                executed_operation = 'started_backup'

            except Exception as ex:
                LOGGER.error('failed to start backup')
                LOGGER.exception(ex)
                cc.report_to_control_center("fail", "failed to start backup: " + str(ex))

        elif action == 'prune':
            try:
                LOGGER.info("Starting to prune repository")
                borg_commands.break_lock(borg_commands.REMOTE_REPO)
                offsite_archive_process = borg_commands.prune(borg_commands.REMOTE_REPO)
                offsite_archive_process_started = datetime.now()
                LOGGER.info("Prune process has pid {}".format(offsite_archive_process.pid))
                cc.report_to_control_center("incident", "pruning started")
                executed_operation = 'started_prune'
            except Exception as ex:
                LOGGER.error('failed to start prune process')
                LOGGER.exception(ex)
                cc.report_to_control_center("incident", "pruning failed: {}".format(str(ex)))

        elif action == 'idle':
            if not mount_process:
                mount(True)
                executed_operation = 'mount'
            is_allowed_to_remount = True
    else:
        action = "backup_ongoing"

    ip_address = environment.get_ip_address()

    device_api.device_update_status(
        environment.get_safeplan_id(),
        DeviceStatus(
            ip_address=ip_address,
            last_backup=last_backup_timestamp,
            last_pruned=last_pruned,
            last_action=executed_operation,
            last_action_as_of=datetime.utcnow()
        ))

    LOGGER.info("worker finished. Executed operation: {}".format(executed_operation))
    return executed_operation


def get_last_backed_up(repo_list):
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
            json.dump(repo_list, outfile)

        last_pruned = None
        prune_logfile = "{}/backup_prune.log".format(environment.PATH_WORK)
        if os.path.exists(prune_logfile):
            with open(prune_logfile, 'r') as f:
                if 'terminating with success' in f.read():
                    last_pruned = datetime.fromtimestamp(os.path.getmtime(prune_logfile))

        last_backup_timestamp = get_last_backed_up(repo_list)
        last_modified = None
        try:
            last_modified = dateutil.parser.parse(repo_info['repository']['last_modified'])
        except:
            pass

        age = int((datetime.now() - last_backup_timestamp).total_seconds() / 3600) if last_backup_timestamp else -1

        if age >= 0:
            description = "Last backup occurred at {}. As of {} it's {} hour(s) old. Last pruned: {}".format(
                strdatetime(last_backup_timestamp), strdatetime(datetime.now()), age, strdatetime(last_pruned))
        else:
            description = "No backup yet (or a long-running backup is currently ongoing)"

            # append df -h output of the backup directory to the description
        df = subprocess.Popen(["df", "-h", environment.PATH_BACKUP], stdout=subprocess.PIPE)
        description += "\n" + df.communicate()[0].decode('UTF-8')

        LOGGER.info("Repository status has been updated. %s", description)

        cc.report_to_control_center("ok" if age >= 0 and age < 24 else "fail", description)

        return last_backup_timestamp, last_modified, last_pruned
    except Exception as ex:
        LOGGER.error("failed to retrieve status of offsite repository")
        LOGGER.exception(ex)
        cc.report_to_control_center("fail", "failed to retrieve status of offsite repository: " + str(ex))


def get_current_offsite_process():
    global offsite_archive_process
    global offsite_archive_process_started

    return offsite_archive_process, offsite_archive_process_started


def strdatetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def is_a_mount_point(path):
    cmd = "mountpoint -q {}".format(path)
    returncode = subprocess.call(cmd, shell=True)
    if returncode == 0:
        return True
    else:
        return False


def unmount():
    global mount_process

    if mount_process != None:
        LOGGER.info("Unmounting mount process {}".format(mount_process.pid))

    borg_commands.unmount()

    mount_process = None
    cc.report_to_control_center("incident", "archive unmounted")


def mount(forced=False):
    global mount_process

    if not forced and not is_allowed_to_remount:
        LOGGER.info("Currently not allowed to mount...")
        return

    # If there is a running mount_process, exit
    if mount_process and mount_process.poll() == None:
        LOGGER.info("Offsite archive already mounted by process {}".format(mount_process.pid))
        return

    try:
        unmount()
        LOGGER.info("Now mounting offsite archive")
        mount_process = borg_commands.mount(borg_commands.REMOTE_REPO)
        LOGGER.info("Offsite archive mounted by process {}".format(mount_process.pid))
        cc.report_to_control_center("incident", "archive mounted")
    except Exception as ex:
        LOGGER.error('failed to mount offsite archive')
        LOGGER.exception(ex)
        cc.report_to_control_center("incident", "failed to mount archive (" + str(ex) + ")")


def touch_backup():
    try:
        touch_file = os.path.join(environment.PATH_BACKUP, ".safeplan-modified")
        with open(touch_file, mode='w') as file:
            file.write(strdatetime(datetime.now()))
    except Exception as ex:
        message = "failed to write to {}".format(touch_file)
        LOGGER.error(message)
        LOGGER.exception(ex)
        cc.report_to_control_center("fail", message + ": " + str(ex))


def tail(f, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        # Removed this line because it was redundant the while will catch
        # it, I left it for history
        # if len(lines_found) > lines:
        #    break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]
