
from ... intermidiate.symtab_if import SynTabEntryIF, SymTabIF
from ..activation_record_if import ActivationRecordIF
from .. memory_if import MemoryMapIF, create_memory_map


class ActivationRecord(ActivationRecordIF):

    def __init__(self, routine_id: SynTabEntryIF):
        self.link:ActivationRecordIF = None
        self.symtab: SymTabIF = routine_id.get_attribute('ROUTINE_SYMTAB')
        self.routine_id: SynTabEntryIF = routine_id
        self.nesting_level: int = self.symtab.get_nesting_level()
        self.memory_map: MemoryMapIF = create_memory_map(self.symtab)

    def get_routine_id(self) -> SynTabEntryIF:
        return self.routine_id

    def get_cell(self, name: str):
        return self.memory_map.get_cell(name)

    def get_all_names(self) -> list:
        return self.memory_map.get_all_names()

    def get_nesting_level(self) -> int:
        return self.nesting_level

    def linked_to(self):
        return self.link

    def make_linked_to(self, ar: ActivationRecordIF):
        self.link = ar
        return ar

