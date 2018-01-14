# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.device_info import DeviceInfo  # noqa: E501
from swagger_server.models.device_initialization_info import DeviceInitializationInfo  # noqa: E501
from swagger_server.test import BaseTestCase


class TestDeviceController(BaseTestCase):
    """DeviceController integration test stubs"""

    def test_get_device(self):
        """Test case for get_device

        
        """
        response = self.client.open(
            '/safeplan/backup-agent/1.0.0/device',
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_initializes_the_device_with_it&#39;s_safeplan_id(self):
        """Test case for initializes_the_device_with_it's_safeplan_id

        
        """
        device = DeviceInitializationInfo()
        response = self.client.open(
            '/safeplan/backup-agent/1.0.0/device/initialization',
            method='POST',
            data=json.dumps(device),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
