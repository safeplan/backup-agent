
from safeplan.api_client import ApiClient
from safeplan.api import DeviceApi
import environment

client = ApiClient()
client.set_default_header("device_secret",environment.get_device_secret())

device_api = DeviceApi(client)


