import connexion
import os

def get_details():  # noqa: E501
    if not 'SAFEPLAN_ID' in os.environ:
        return {'error' : 'SAFEPLAN_ID not set'}, 500

    return {'device_id' : os.environ['SAFEPLAN_ID']}


def initialize(device=None):  # noqa: E501
    """initializes_the_device_with_it&#39;s_safeplan_id

     # noqa: E501

    :param device: 
    :type device: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        pass
    return 'do some magic!'
