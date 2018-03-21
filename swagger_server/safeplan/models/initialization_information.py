# coding: utf-8

"""
    device-api

    safeplan device api

    OpenAPI spec version: 1.0.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


from pprint import pformat
from six import iteritems
import re


class InitializationInformation(object):
    """
    NOTE: This class is auto generated by the swagger code generator program.
    Do not edit the class manually.
    """


    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'rsa_public_key': 'str'
    }

    attribute_map = {
        'rsa_public_key': 'rsa_public_key'
    }

    def __init__(self, rsa_public_key=None):
        """
        InitializationInformation - a model defined in Swagger
        """

        self._rsa_public_key = None

        self.rsa_public_key = rsa_public_key

    @property
    def rsa_public_key(self):
        """
        Gets the rsa_public_key of this InitializationInformation.

        :return: The rsa_public_key of this InitializationInformation.
        :rtype: str
        """
        return self._rsa_public_key

    @rsa_public_key.setter
    def rsa_public_key(self, rsa_public_key):
        """
        Sets the rsa_public_key of this InitializationInformation.

        :param rsa_public_key: The rsa_public_key of this InitializationInformation.
        :type: str
        """
        if rsa_public_key is None:
            raise ValueError("Invalid value for `rsa_public_key`, must not be `None`")

        self._rsa_public_key = rsa_public_key

    def to_dict(self):
        """
        Returns the model properties as a dict
        """
        result = {}

        for attr, _ in iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """
        Returns the string representation of the model
        """
        return pformat(self.to_dict())

    def __repr__(self):
        """
        For `print` and `pprint`
        """
        return self.to_str()

    def __eq__(self, other):
        """
        Returns true if both objects are equal
        """
        if not isinstance(other, InitializationInformation):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """
        Returns true if both objects are not equal
        """
        return not self == other