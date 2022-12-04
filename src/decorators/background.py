import functools
import inspect
import threading
from typing import Optional, Callable


def background(thread_name: Optional[str or Callable] = None):
    """
    Inicia la función que tiene este decorator en un nuevo thread.
    @param thread_name: El nombre del thread.
    """
    def wrapper(func):
        @functools.wraps(func)  # Mantener los parámetros.
        def wrap(*args, **kwargs):
            thread = threading.Thread(target=func, args=args, kwargs=kwargs, name=thread_name, daemon=True)
            thread.start()
            return thread

        # https://stackoverflow.com/questions/39926567find/python-create-decorator-preserving-function-arguments
        wrap.__signature__ = inspect.signature(func)
        return wrap

    # Aplicar el nombre dentro de la llamada (), por lo que hay que detectar cuando se llama al decorator con ().
    if isinstance(thread_name, Callable):
        my_function = thread_name
        thread_name = None
        return wrapper(my_function)
    # Si el decorator no tenía ().
    return wrapper
