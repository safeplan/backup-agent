import connexion
import six

from swagger_server.models.device_info import DeviceInfo  # noqa: E501
from swagger_server.models.device_initialization_info import DeviceInitializationInfo  # noqa: E501
from swagger_server import util


def get_device():  # noqa: E501
    """get_device

    returns the details of the device # noqa: E501


    :rtype: DeviceInfo
    """
    return 'do some magic!'


def initialize_device(device=None):  # noqa: E501
    """initializes_the_device_with_it&#39;s_safeplan_id

     # noqa: E501

    :param device: 
    :type device: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        device = DeviceInitializationInfo.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
