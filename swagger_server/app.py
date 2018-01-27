#!/usr/bin/env python3
"""
Safeplan backup agent
"""

import logging
import os
import sys
import signal
import connexion
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import initializer
from worker import do_work

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("main")

SCHEDULER = BackgroundScheduler()

def shutdown_handler(signum, frame):
    """stops the scheduler when shutting down"""
    LOGGER.info("Received signal %d (%s), shutting down scheduler", signum, str(frame))
    SCHEDULER.shutdown(wait=False)
    sys.exit(1)

def start_swagger():
    """Starting the swagger-served api"""
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.add_api('swagger.yaml', arguments={'title': 'safeplan-backup-agent'})
    CORS(app.app)
    app.run(port=8080, debug=True if os.environ.get('DEBUG',0) == "1" else False)



if __name__ == '__main__':
    if not 'SAFEPLAN_ID' in os.environ or os.environ['SAFEPLAN_ID'] == 'NOT_SET':
        sys.exit('SAFEPLAN_ID environment variable not set, exiting.')

    if not 'HOST_IP' in os.environ or os.environ['HOST_IP'] == 'NOT_SET':
        sys.exit('HOST_IP environment variable not set, exiting.')

    LOGGER.info("starting safeplan backup agent for device {}".format(os.environ['SAFEPLAN_ID'])) 
    
    initializer.initialize()


    SCHEDULER.start()
    SCHEDULER.add_job(do_work, 'interval', seconds=60, id='worker')
    signal.signal(signal.SIGTERM, shutdown_handler)

    start_swagger()
