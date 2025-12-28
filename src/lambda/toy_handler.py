import logging
import os

from utils.logger import setup_logger


# def toy_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
def toy_handler(a, b):
    print('>>>>> toy_handler.py:6 "a"')
    print(a)
    print('>>>>> toy_handler.py:8 "b"')
    print(b)
    print("This is a toy handler function.")
    watchlist = os.environ.get("WATCHLIST", "paila")
    print('>>>>> toy_handler.py:8 "watchlist"')
    print(watchlist)
    test_variable = os.environ.get("TEST_VARIABLE", "paila_pero_mas_chido")
    print('>>>>> toy_handler.py:15 "test_variable"')
    print(test_variable)
    lambda_function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    print('>>>>> toy_handler.py:18 "lambda_function_name"')
    print(lambda_function_name)

    logger = setup_logger(
        name="toy_handler",
        level=logging.DEBUG,
    )

    logger.debug("Debug level log from toy_handler.")
    logger.info("Info level log from toy_handler.")
