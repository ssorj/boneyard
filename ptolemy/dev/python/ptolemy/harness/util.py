import yaml

from ptolemy.common.util import *

def init_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
