#!/usr/bin/env python3
import logging
import sys
import signal
import connexion
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import environment
import initializer

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("main")

SCHEDULER = BackgroundScheduler()

def shutdown_handler(signum, frame):
    """stops the scheduler when shutting down"""
    SCHEDULER.shutdown(wait=False)
    sys.exit(1)

def start_swagger():
    """Starting the swagger-served api"""
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.add_api('swagger.yaml', arguments={'title': 'safeplan-backup-agent'})
    CORS(app.app)
    app.run(port=8080)

def worker():
    """Background worker"""
    if not environment.is_initialized():
        initializer.initialize() 

if __name__ == '__main__':
    LOGGER.info("starting safeplan backup agent")
    
    worker()
    SCHEDULER.start()
    SCHEDULER.add_job(worker, 'interval', seconds=60, id='worker')
    signal.signal(signal.SIGTERM, shutdown_handler)

    start_swagger()
