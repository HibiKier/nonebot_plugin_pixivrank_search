import time
from collections import defaultdict


class UserExistLimiter:
    def __init__(self):
        self.mbool = defaultdict(bool)
        self.time = time.time()

    def set_true(self, key):
        self.time = time.time()
        self.mbool[key] = True

    def set_false(self, key):
        self.mbool[key] = False

    def check(self, key):
        if time.time() - self.time > 30:
            self.set_false(key)
            return False
        return self.mbool[key]
