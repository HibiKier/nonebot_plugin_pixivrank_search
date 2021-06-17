from collections import defaultdict
import time


class UserExistLimiter:
    def __init__(self):
        self.mbool = defaultdict(bool)
        self.time = time.time()

    def set_True(self, key):
        self.time = time.time()
        self.mbool[key] = True

    def set_False(self, key):
        self.mbool[key] = False

    def check(self, key):
        if time.time() - self.time > 30:
            self.set_False(key)
            return False
        return self.mbool[key]


def is_number(s) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


