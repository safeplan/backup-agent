# pylint: disable=C0111

import os
import shutil
import unittest
import worker
import mock
from safeplan.models import StatusInformation
from datetime import datetime

class TestWorker(unittest.TestCase):

     @mock.patch('safeplan_server.device_api.device_get_details')
     def test_do_nothing_if_device_is_not_initialized(self, device_get_details):
        device_get_details.return_value = StatusInformation(server_time = datetime.utcnow,status='provisioned',as_of=datetime.now() )
        executed_operation = worker.do_work()
        self.assertEqual('noop',executed_operation)


     @mock.patch('safeplan_server.device_api.device_get_details')
     def test2(self, device_get_details):
        device_get_details.return_value = StatusInformation(server_time = datetime.utcnow,status='provisioned',as_of=datetime.now() )
        executed_operation = worker.do_work()
        self.assertEqual('noop',executed_operation)
