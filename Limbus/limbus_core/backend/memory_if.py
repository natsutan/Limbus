from abc import ABCMeta, abstractmethod

from .. intermidiate.symtab_if import SymTabIF
from .memory .memory_map import MemoryMap

# Factory 関数
def create_runtime_stack():
    return RuntimeStack()


def create_runtime_display():
    return RuntimeDisplay()


def create_active_recode():
    return ActiveRecord()


def create_memory_map(symtab: SymTabIF):
    return MemoryMap(symtab)


def create_cell(foo):
    return Cell()


class MemoryMapIF(metaclass=ABCMeta):
    @abstractmethod
    def get_cell(self, name: str):
        raise NotImplementedError()

    @abstractmethod
    def get_all_names(self) -> list:
        raise NotImplementedError()


