import logging
import os
import time

def setup_logging():
    AWS_LAMBDA_FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", None)
    if not os.path.exists("logging") and AWS_LAMBDA_FUNCTION_NAME is None:
        os.makedirs("logging")
    logging.basicConfig(
        level=logging.DEBUG,
        filename=f"logging/lambda_{int(time.time())}.log",
    ) # this only works in local, lambda already has a handler attached to root logger
    logging.getLogger().setLevel(logging.DEBUG) # set root logger level in lambda, by default it's WARNING
    # default lambda logging format: '[%(levelname)s] %(asctime)s.%(msecs)03dZ %(aws_request_id)s %(message)s'
    # custom formatter to include logger name instead of aws_request_id
    logging.getLogger().handlers[0].setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s.%(msecs)03dZ %(name)s %(message)s'))
