

from abc import abstractmethod


class JobProcessor:
    def __init__(self):
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass

    @abstractmethod
    def create_job(self, config: dict) -> dict:
        pass

