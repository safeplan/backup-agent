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
        'onsite_info' : from_file("onsite-info.json"),
        'onsite_list' : from_file("onsite-list.json"),
        'offsite_info' : from_file("offsite-info.json"),
        'offsite_list' : from_file("offsite-list.json")}


def from_file (f):
    filename = "{}/{}".format(environment.PATH_WORK,f)
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return {}
