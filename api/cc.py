import logging
import os
import environment
import requests

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()


def report_to_control_center(status, message):
    LOGGER.info("report to control center: {} {}".format(status, message))
    if environment.get_cc_api_key():
        url = "https://control-center.armstrongconsulting.com/api/agent/SAFEPLAN_{}/{}?parentApiKey={}".format(
            environment.get_safeplan_id(), status, environment.get_cc_api_key())
        try:
            requests.post(url=url, data=message)
        except Exception as ex1:
            LOGGER.error('Failed to report to control center')
            LOGGER.exception(ex1)
    else:
        LOGGER.error("can't report to control center: cc_api_key is not set")
        