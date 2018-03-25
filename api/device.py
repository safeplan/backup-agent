"""
Device controller
"""
import os
import logging
import connexion
import environment
import json
import worker

LOGGER = logging.getLogger()

def get_details():  # noqa: E501
    """returns the current details of the device"""
    running = []
    process, running_since = worker.get_current_offsite_process()
    if process:
        running.append({'pid' : process.pid, 'running_since':running_since, 'type' : 'offsite'})

    return {'device_id' : environment.get_safeplan_id(), 
        'mode' : environment.get_forced_mode() if environment.get_forced_mode() != None else environment.get_current_mode(),
        'running_process' : running,
        'offsite_info' : from_file("offsite-info.json"),
        'offsite_list' : from_file("offsite-list.json")}

def set_mode(mode):
    if mode == 'force_backup':
        environment.set_forced_mode('backup')
    elif mode == 'force_idle':
        environment.set_forced_mode('idle')
    elif mode == 'force_cleanup':
        environment.set_forced_mode('cleanup')
    else:
        environment.set_forced_mode(None)

    return get_details();


def from_file (f):
    filename = "{}/{}".format(environment.PATH_WORK,f)
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return {}
