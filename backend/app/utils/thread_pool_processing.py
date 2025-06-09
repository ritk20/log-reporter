from concurrent.futures.thread import ThreadPoolExecutor
import os

EXECUTOR = ThreadPoolExecutor(max_workers=int(os.getenv("THREAD_POOL_SIZE", 4)))
def run_in_thread_pool(func, *args, **kwargs):
    """
    Run a function in the thread pool executor.
    
    :param func: The function to run.
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :return: Future object representing the execution of the function.
    """
    return EXECUTOR.submit(func, *args, **kwargs)