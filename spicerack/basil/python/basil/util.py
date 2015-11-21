import os
from StringIO import StringIO

class StringCatalog(object):
    def __init__(self, filename):
        self.__strings = dict()

        path = os.path.splitext(filename)[0] + ".strings"

        try:
            file = open(path)
            self.parse(file)
        finally:
            file.close()

    def get(self, key):
        return self.__strings.get(key)

    def parse(self, file):
        key = None
        writer = StringIO()

        for line in file:
            line = line[0:-1]

            if line.startswith("[") and line.endswith("]"):
                if key:
                    self.__strings[key] = writer.getvalue().rstrip()

                writer = StringIO()

                key = line[1:-1]

                continue

            writer.write(line)
            writer.write("\n")

        self.__strings[key] = writer.getvalue().rstrip()
