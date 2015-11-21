try:
    from string import partition, rpartition
    def partition(str, sep):
        return str.partition(sep)

    def rpartition(str, sep):
        return str.rpartition(sep)

except ImportError:
    def partition(str, sep):
        i = str.find(sep)
        if i >= 0:
            return (str[:i], sep, str[i+1:])
        else:
            return (str, "", "")

    def rpartition(str, sep):
        i = str.rfind(sep)
        if i >= 0:
            return (str[:i], sep, str[i+1:])
        else:
            return ("", "", str)
