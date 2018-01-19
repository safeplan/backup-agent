"""Initializing operations"""

import logging
import environment
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend



LOGGER = logging.getLogger("initializer")

def initialize():
    """Initializes the backup-agent"""
 
    if not os.path.exists(environment.PATH_CONFIG):
        LOGGER.warning("Creating config path %s", environment.PATH_CONFIG)
        os.makedirs(environment.PATH_CONFIG, 0o700)

    filename_private_key = os.path.join(environment.PATH_CONFIG,"id_rsa")
    filename_public_key = os.path.join(environment.PATH_CONFIG,"id_rsa.pub")
    if not os.path.exists(filename_private_key):
        LOGGER.warning("Creating ssh keys")
        key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=2048)

        # get public key in OpenSSH format
        public_key = key.public_key().public_bytes(serialization.Encoding.OpenSSH, \
            serialization.PublicFormat.OpenSSH)

        # get private key in PEM container format
        pem = key.private_bytes(encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption())

        # decode to printable strings
        private_key_str = pem.decode('utf-8')
        public_key_str = public_key.decode('utf-8')

        with open(filename_private_key, mode='w') as f:
            f.write(private_key_str)

        with open(filename_public_key, mode='w') as f:
            f.write(public_key_str)

        os.chmod(filename_public_key, 0o444)
        os.chmod(filename_private_key, 0o400)
    
        
if __name__ == '__main__':
    initialize()