"""Initializing operations"""

import logging
import environment
from safeplan.apis import DeviceApi
from safeplan.models import DeviceStatus

LOGGER = logging.getLogger()
SAFEPLAN = DeviceApi()

def do_work():
    """Background worker"""
    LOGGER.info("starting worker.")

    SAFEPLAN.device_update_status(
        environment.get_safeplan_id(),
        DeviceStatus(ip_address = environment.get_ip_address()))

    

    LOGGER.info("worker finished.")
    