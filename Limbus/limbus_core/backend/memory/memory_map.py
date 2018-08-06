
from .. memory_if import MemoryMapIF, create_cell

from ... intermidiate.type_impl import Definition, TypeSpec
from ... intermidiate.symtab_if import SymTabIF


class MemoryMapImpl(MemoryMapIF):
    def __init__(self, symtab: SymTabIF):
        self.map = {}
        entries = symtab.get_sorted_entries()
        self.memory_factory =

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




    def allocate_cell_value(self, typespec):
        return None