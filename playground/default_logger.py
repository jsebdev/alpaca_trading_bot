import logging

logger = logging.getLogger()

logging.basicConfig(filename='myapp.log', level=logging.INFO)

logger.info("Default logger has been set up.")
