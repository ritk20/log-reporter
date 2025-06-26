import time
import functools
from typing import Callable, Any, Dict

def performance_monitor(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            print(f"[FUNCTION]: {func.__name__}: {execution_time:.6f} seconds")
            return result
        except Exception as e:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            print(f"{func.__name__} failed after {execution_time:.6f} seconds: {e}")
            raise
    return wrapper
