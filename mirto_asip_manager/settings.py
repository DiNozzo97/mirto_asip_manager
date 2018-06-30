import logging
import logging.handlers

LOG_FILENAME = '/var/log/mirto_robot_logs.log'

# Logger settings
logging.root.handlers = []

FORMAT = '%(asctime)s : %(levelname)s : %(message)s\r'

logging.basicConfig(format=FORMAT, level=logging.DEBUG,
                    filename=LOG_FILENAME)

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)  # this is only if we want to error logs be printed out to console

# Set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : [%(filename)s:%(lineno)d] : %(levelname)s - %(message)s', '%m-%d %H:%M:%S')

console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=10000000, backupCount=2)

logging.getLogger("").addHandler(handler)
