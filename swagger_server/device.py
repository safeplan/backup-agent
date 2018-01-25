"""
Device controller
"""
import os
import logging
import connexion

LOGGER = logging.getLogger("DeviceController")

def get_details():  # noqa: E501
    """returns the current details of the device"""
    if not 'SAFEPLAN_ID' in os.environ:
        return {'error' : 'SAFEPLAN_ID not set'}, 500

    return {'device_id' : os.environ['SAFEPLAN_ID']}



