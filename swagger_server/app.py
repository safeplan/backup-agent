#!/usr/bin/env python3
"""
Safeplan backup agent
"""

import logging
import logging.handlers
from logutils import HttpLoggingHandler
from logutils import JsonLogFormatter
import os
import sys
import signal
import connexion
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import initializer
from worker import do_work
import environment

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()

SCHEDULER = BackgroundScheduler()

def shutdown_handler(signum, frame):
    """stops the scheduler when shutting down"""
    LOGGER.info("Received signal %d (%s), shutting down scheduler", signum, str(frame))
    SCHEDULER.shutdown(wait=False)
    sys.exit(1)

def start_swagger():
    """Starting the swagger-served api"""
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.add_api('swagger.yaml', arguments={'host':'{}:8080'.format(environment.get_ip_address())} )
    CORS(app.app)
    app.run(port=8080, debug=True if os.environ.get('DEBUG',0) == "1" else False)

if __name__ == '__main__':
    if not environment.get_safeplan_id():
        sys.exit('SAFEPLAN_ID environment variable not set, exiting.')

    all_paths_ok, problematic_path = environment.check_paths()
    if not all_paths_ok:
        sys.exit("Unable to access path {0}".format(problematic_path))
        

    logging.basicConfig(level=logging.INFO)


    #Log (rotated) to backup-agent.log
    logfile = os.path.join(environment.PATH_WORK, "backup-agent.log")
    fileHandler = logging.handlers.RotatingFileHandler(logfile, maxBytes=50000000, backupCount=5)
    fileHandler.setFormatter(logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"))
    LOGGER.addHandler(fileHandler)

    #TODO: http log handler
    #httpHandler = HttpLoggingHandler()
    #httpHandler.setFormatter(JsonLogFormatter())
    #LOGGER.addHandler(httpHandler)

    LOGGER.info("starting safeplan backup agent for device %s",os.environ['SAFEPLAN_ID']) 

    if initializer.initialize():
        SCHEDULER.start()
        SCHEDULER.add_job(do_work, 'interval', seconds=environment.EXECUTE_WORKER_EVERY_SECONDS, id='worker')
        signal.signal(signal.SIGTERM, shutdown_handler)

        do_work()

        start_swagger()
    else:
        sys.exit('Initializing failed, exiting.')
