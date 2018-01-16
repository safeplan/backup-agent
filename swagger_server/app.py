#!/usr/bin/env python3
import connexion
from flask_cors import CORS

def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.add_api('swagger.yaml', arguments={'title': 'safeplan-backup-agent'})
    CORS(app.app)
    app.run(port=8080)

if __name__ == '__main__':
    main()
