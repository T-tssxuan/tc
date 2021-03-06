import time
import inspect

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log(info):
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    rst = bcolors.OKGREEN
    rst += time.strftime('%H:%M:%S') + ' '
    rst += str(module.__name__) + '-->'
    rst += str(inspect.stack()[1][3]) + ': '
    rst += str(info)
    rst += bcolors.ENDC
    print(rst)

def debug(info):
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    rst = bcolors.OKBLUE
    rst += time.strftime('%H:%M:%S') + ' '
    rst += str(module.__name__) + '-->'
    rst += str(inspect.stack()[1][3]) + ': '
    rst += str(info)
    rst += bcolors.ENDC
    print(rst)
