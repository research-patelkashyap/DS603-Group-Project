import hashlib

class Blob:
    def __init__(self, content: bytes):
        self.content = content
        self.hash = self.compute_hash()

    def compute_hash(self):
        return hashlib.sha1(self.content).hexdigest()
