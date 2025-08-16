from functools import wraps
from time import time

# simple function process timer
def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        time_start = time()
        output = func(*args, **kwargs)
        time_end = time()
        print(f"time: {time_end - time_start:.6f} seconds")
        return output
    return wrapper

# decorator used to indicate rigorousness of unit tests
def test_status(status: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper._test_status = status  
        return wrapper
    return decorator


