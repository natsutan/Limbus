from abc import ABCMeta, abstractmethod


class ActivationRecordIF(metaclass=ABCMeta):
    @abstractmethod
    def get_routine_id(self):
        raise NotImplementedError()

    @abstractmethod
    def get_cell(self, name: str):
        raise NotImplementedError()

    @abstractmethod
    def get_all_names(self) -> list:
        raise NotImplementedError()

    @abstractmethod
    def get_nesting_level(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def linked_to(self):
        raise NotImplementedError()

    @abstractmethod
    def make_linked_to(self, ar):
        raise NotImplementedError()

