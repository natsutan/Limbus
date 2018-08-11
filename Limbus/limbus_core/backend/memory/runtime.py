import sys
sys.path.append('limbus_core\\backend')

from runtime_if import RuntimeDisplayIF, RuntimeStackIF
from activation_record_if import ActivationRecordIF


class RuntimeStack(RuntimeStackIF):
    def __init__(self):
        from memory_if import create_runtime_display
        self.display: RuntimeDisplayIF = create_runtime_display()
        self.records: list = []

#    def records(self):
#        return self.records

    def get_topmost(self, nesting_level: int) -> ActivationRecordIF:
        return self.display.get_active_record(nesting_level)

    def current_nesting_level(self):
        index = len(self.records) - 1
        if index >= 0:
            return self.records[index].get_nesting_level()
        else:
            return -1

    def push(self, ar: ActivationRecordIF):
        nesting_level = ar.get_nesting_level()
        self.records.append(ar)
        self.display.call_update(nesting_level, ar)

    def pop(self):
        self.display.return_update(self.current_nesting_level())
        self.records.pop()


class RuntimeDisplay(RuntimeDisplayIF):
    def __init__(self):
        # dummy element 0
        self.list = [None, ]

    def get_active_record(self, nesting_level: int) -> ActivationRecordIF:
        return self.list[nesting_level]

    def call_update(self, nesting_level: int, ar: ActivationRecordIF):
        if nesting_level >= len(self.list):
            self.list.append(ar)
        else:
            prev_ar: ActivationRecordIF = self.list[nesting_level]
            self.list[nesting_level] = ar.make_linked_to(prev_ar)

    def return_update(self, nesting_level: int):
        top_index: int = len(self.list)
        ar: ActivationRecordIF = self.list[nesting_level]
        prev_ar: ActivationRecordIF = ar.linked_to()

        if not ar.is_dummy():
            self.list[nesting_level] = prev_ar
        elif nesting_level == top_index:
            self.list.pop(top_index)
