import os
import wooly

class ResourceFinder(object):
    def __init__(self):
        self.dirs = list()
        self.whitelists = dict() # dir => (name1, name2, ...)

    def add_dir(self, dir):
        if not os.path.isdir(dir):
            return

        self.dirs.append(dir)
        self.whitelists[dir] = set(os.listdir(dir))

    def find(self, name):
        file = None

        for dir in self.dirs:
            whitelist = self.whitelists[dir]

            if name in whitelist:
                try:
                    path = os.path.join(dir, name)
                    file = open(path, "r")
                except IOError:
                    pass

        return file
