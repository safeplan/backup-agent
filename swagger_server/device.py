"""
Device controller
"""
import os
import logging
import connexion
import environment

LOGGER = logging.getLogger("DeviceController")

def get_details():  # noqa: E501
    """returns the current details of the device"""

    return {'device_id' : environment.get_safeplan_id()}


def initialize(device=None):  # noqa: E501
    """Initializes the device"""
    LOGGER.info(device)
    if connexion.request.is_json:
        pass
    return 'do some magic!'
