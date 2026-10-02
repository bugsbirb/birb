import os

from cryptography.fernet import Fernet

secret = os.getenv("FERNET_SECRET")
if secret is None:
    raise RuntimeError("'FERNET_SECRET' env variable not set.")
fernet = Fernet(secret)


class Cytography:
    def __init__(self):
        self.__init__()

    def encrypt(self, string: str):
        return fernet.encrypt(string.encode())

    def decrypt(self, string: str):
        return fernet.decrypt(string.encode())

    def generate(self):
        return fernet.generate_key()
