from ... intermidiate.type_impl import Definition, TypeSpec, TypeForm
from ... intermidiate.symtab_if import SymTabIF

from .. memory_if import MemoryMapIF, create_cell, create_memory_map


class MemoryMap(MemoryMapIF):
    def __init__(self, symtab: SymTabIF):
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

    def allocate_cell_value(self, typespec: TypeSpec):
        form: TypeForm = typespec.get_form()

        if form == TypeForm.ARRAY:
            return self.allocate_array_cells(typespec)
        elif form == TypeForm.RECORD:
            return self.allocate_record_map(typespec)
        else:
            return None

    def allocate_array_cells(self, typespec: TypeSpec):
        element_count: int = typespec.get_attribute('ARRAY_ELEMENT_COUNT')
        elem_type: TypeSpec = typespec.get_attribute('ARRAY_ELEMENT_TYPE')
        allocation: list = []

        for i in range(element_count):
            new_cell = create_cell(self.allocate_cell_value(elem_type))
            allocation.append(new_cell)

        return allocation

    @staticmethod
    def allocate_record_map(typespec: TypeSpec):
        symtab: SymTabIF = typespec.get_attribute('RECORD_SYMTAB')
        memory_map: MemoryMapIF = create_memory_map(symtab)

        return memory_map

