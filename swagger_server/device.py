"""
Device controller
"""
import os
import logging
import connexion
import environment
import json

LOGGER = logging.getLogger()

def get_details():  # noqa: E501
    """returns the current details of the device"""

    return {'device_id' : environment.get_safeplan_id(), 
        'mode' : environment.get_forced_mode() if environment.get_forced_mode() != None else environment.get_current_mode(),
        'offsite_info' : from_file("offsite-info.json"),
        'offsite_list' : from_file("offsite-list.json")}

def set_mode(mode):
    if mode == 'force_backup':
        environment.set_forced_mode('backup')
    elif mode == 'force_idle':
        environment.set_forced_mode('idle')
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
