from ... intermidiate.type_impl import Definition, TypeSpec, TypeForm
from ... intermidiate.symtab_if import SymTabIF

#from .. memory_if import MemoryMapIF, create_cell, create_memory_map
from .. runtime_if import CellIF


class Cell(CellIF):
    def __init__(self, value):
        self.value = None

    @property
    def value(self):
        return self.value

    @value.setter
    def value(self, v):
        self.value = v


