import threading
from typing import Optional, Callable, Tuple


class ThreadExecutor:
    def __init__(self):
        self.__name: str = self.__class__.__name__
        self.__stopped_looping: bool = False
        self._executor_thread: Optional[threading.Thread] = None

    def is_on_thread(self) -> bool:
        return threading.current_thread() is self._executor_thread

    def should_keep_looping(self) -> bool:
        return not self.__stopped_looping

    def get_name(self) -> str:
        return self.__name

    def stop(self) -> None:
        self.__stopped_looping = True

    def start(self) -> threading.Thread:
        self._executor_thread = self.start_thread(self.loop, (), self.get_name())
        return self._executor_thread

    def loop(self) -> None:
        while self.should_keep_looping():
            self.tick()

    def tick(self) -> None:
        raise NotImplementedError()

    def join(self) -> None:
        if self._executor_thread is None:
            raise RuntimeError()
        self._executor_thread.join()

    @staticmethod
    def start_thread(func: Callable, args: Tuple, name: str or None = None) -> threading.Thread:
        thread = threading.Thread(target=func, args=args, name=name, daemon=True)
        thread.start()
        return thread
