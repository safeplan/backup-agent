from logging import Handler
from logging import Formatter
import json
from datetime import datetime
import requests


class HttpLoggingHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        return requests.post('http://localhost:5000/xxxxx',
                             log_entry, headers={"Content-type": "application/json"}).content

class JsonLogFormatter(Formatter):
    def format(self, record):
        msg = super(JsonLogFormatter, self).format(record)
        data = {'message': msg,
                'filename': record.filename,
                'level':record.levelname,
                'module':record.module,
                'created': datetime.utcfromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'sent': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                }
 
  
        return json.dumps(data)