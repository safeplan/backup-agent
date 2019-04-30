#!/usr/bin/env python3
"""
Safeplan backup agent
"""

import logging
import logging.handlers
import os
import sys
import signal
import connexion
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import initializer
import environment
from flask import abort, send_file, render_template, jsonify, request, send_from_directory, redirect
import time
import worker
import requests
import cc

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()

SCHEDULER = BackgroundScheduler()

app = connexion.App(__name__, specification_dir='./swagger/')

FILE_BASE_DIR = os.environ.get("SAFEPLAN_BROWSE_BASE_DIR", '/var/safeplan/history/archives')


@app.route('/history', defaults={'req_path': ''})
@app.route('/history/<path:req_path>')
def dir_listing(req_path):

    worker.mount()

    # Joining the base and the requested path
    abs_path = os.path.join(FILE_BASE_DIR, req_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

    # Show directory contents
    files = os.listdir(abs_path)
    return jsonify(files)


@app.route('/browse/<path:path>')
def send_browser(path):
    worker.mount()
    return send_from_directory('browse', path)


@app.route('/browse')
@app.route('/browse/')
def start_browser():
    worker.mount()
    return redirect("/browse/index.html", code=302)


@app.route('/filemanager',  methods=['POST'])
def list_files():
    worker.mount()
    content = request.get_json(silent=True)
    if 'action' in content and 'path' in content and content['action'] == 'list':
        abs_path = os.path.join(FILE_BASE_DIR, content['path'].strip('/'))
        results = []
        if (os.path.exists(abs_path) and os.path.isdir(abs_path)):
            for file in os.listdir(abs_path):
                file_full_path = os.path.join(abs_path, file)
                is_dir = os.path.isdir(file_full_path)
                results.append({
                    "name": file,
                    "rights": ("d" if is_dir else "-") + "r--r--r--",
                    "size": str(os.path.getsize(file_full_path)),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(os.path.getmtime(file_full_path))),
                    "type": "dir" if is_dir else "file"
                }
                )

        return jsonify({"result": results})
    else:
        return jsonify({"result": {"success": False, "error": "unhandled action"}})


@app.route('/filemanager',  methods=['GET'])
def download_file():
    worker.mount()
    if request.args.get('action', '') == 'download':
        abs_path = os.path.join(FILE_BASE_DIR, request.args.get('path', '').strip('/'))
        return send_file(abs_path)

    else:
        return jsonify({"result": {"success": False, "error": "unhandled action"}})


def shutdown_handler(signum, frame):
    #  stops the scheduler when shutting down
    LOGGER.info("Received signal %d, shutting down scheduler", signum)
    cc.report_to_control_center("incident", "backup-agent shutting down (received signal {})".format(signum))
    SCHEDULER.shutdown()
    LOGGER.info("Shutdown completed")


def start_swagger():
    """Starting the swagger-served api"""
    app.add_api('swagger.yaml', arguments={'host': '{}:8080'.format(environment.get_ip_address())})
    CORS(app.app)

    app.run(port=8080, server='tornado', debug=True if os.environ.get('DEBUG', 0) == "1" else False)
    #app.run(port=8080, debug=True)


if __name__ == '__main__':
    if not environment.get_safeplan_id():
        sys.exit('SAFEPLAN_ID environment variable not set, exiting.')

    all_paths_ok, problematic_path = environment.check_paths()
    if not all_paths_ok:
        message = "Unable to access path {0}".format(problematic_path)
        cc.report_to_control_center("fail", message)
        sys.exit(message)

    logging.basicConfig(level=logging.INFO)

    # Log (rotated) to backup-agent.log
    logfile = os.path.join(environment.PATH_WORK, "backup-agent.log")
    fileHandler = logging.handlers.RotatingFileHandler(logfile, maxBytes=50000000, backupCount=5)
    fileHandler.setFormatter(logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"))
    LOGGER.addHandler(fileHandler)

    LOGGER.info("starting safeplan backup agent for device %s", os.environ['SAFEPLAN_ID'])

    if initializer.initialize():
        SCHEDULER.start()
        SCHEDULER.add_job(worker.do_work, 'interval', seconds=environment.EXECUTE_WORKER_EVERY_SECONDS, id='worker')
        signal.signal(signal.SIGTERM, shutdown_handler)

        worker.do_work()

        start_swagger()
    else:
        cc.report_to_control_center("fail", "device initialization failed")
        sys.exit('Initializing failed, exiting.')
