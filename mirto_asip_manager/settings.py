import logging
from logging.handlers import RotatingFileHandler

# Logger settings
logging.root.handlers = []

FORMAT = '%(asctime)s : %(levelname)s : %(message)s\r'

# logging.basicConfig(format=FORMAT, level=logging.DEBUG,
#                     filename='logs.log')

log_formatter = logging.Formatter(FORMAT)
logFile = 'logs.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)  # this is only if we want to error logs be printed out to console

# Set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : [%(filename)s:%(lineno)d] : %(levelname)s - %(message)s','%m-%d %H:%M:%S')

console.setFormatter(formatter)
logging.getLogger("").addHandler(console)
logging.getLogger("").addHandler(my_handler)



# app_log = logging.getLogger('root')
# app_log.setLevel(logging.INFO)
# app_log.addHandler(my_handler)