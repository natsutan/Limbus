from abc import ABCMeta, abstractmethod
import os
print(os.getcwd())
import sys
sys.path.append('limbus_core\\backend\\memory')
from runtime import RuntimeStack, RuntimeDisplay


# Factory 関数
def create_runtime_stack():
    return RuntimeStack()


def create_runtime_display():
    return RuntimeDisplay()


def create_active_recode(routine_id):
    return ActivationRecord(routine_id)


def create_memory_map(symtab):
    return MemoryMap(symtab)


def create_cell(value):
    return Cell(value)


class MemoryMapIF(metaclass=ABCMeta):
    @abstractmethod
    def get_cell(self, name: str):
        raise NotImplementedError()

    @abstractmethod
    def get_all_names(self) -> list:
        raise NotImplementedError()


class MemoryMap(MemoryMapIF):
    def __init__(self, symtab):
        self.map = {}
        entries = symtab.get_sorted_entries()

        for entry in entries:
            defn: Definition = entry.get_definition()

            if defn == Definition.VARIABLE or defn == Definition.FUNCTION or defn == Definition.VAR_PARM or \
                    defn == Definition.FIELD:
                name: str = entry.get_name()
                typespec: TypeSpec = entry.get_typespec()
                self.map[name] = create_cell(self.allocate_cell_value(typespec))
            elif defn == Definition.VAR_PARM:
                name = entry.get_name()
                self.map[name] = create_cell(None)

    def get_cell(self, name: str):
        return self.map[name]

    def get_all_names(self):
        return self.map.keys()

    def allocate_cell_value(self, typespec):
        form: TypeForm = typespec.get_form()

        if form == TypeForm.ARRAY:
            return self.allocate_array_cells(typespec)
        elif form == TypeForm.RECORD:
            return self.allocate_record_map(typespec)
        else:
            return None

    def allocate_array_cells(self, typespec):
        element_count: int = typespec.get_attribute('ARRAY_ELEMENT_COUNT')
        elem_type: TypeSpec = typespec.get_attribute('ARRAY_ELEMENT_TYPE')
        allocation: list = []

        for i in range(element_count):
            new_cell = create_cell(self.allocate_cell_value(elem_type))
            allocation.append(new_cell)

        return allocation

    @staticmethod
    def allocate_record_map(typespec):
        symtab: SymTabIF = typespec.get_attribute('RECORD_SYMTAB')
        memory_map: MemoryMapIF = create_memory_map(symtab)

        return memory_map
