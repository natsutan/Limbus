# -*- coding: utf-8 -*-
from enum import Enum,  auto
from .symtab_if import *


class SymTabKey(Enum):
    CONSTANT_VALUE = auto()
    ROUTINE_CODE = auto()
    ROUTINE_SYMTAB = auto()
    ROUTINE_ICODE = auto()
    ROUTINE_PARMS = auto()
    ROUTINE_ROUTINES = auto()
    DATA_VALUE = auto()


class SymTabStack(SymTabStackIF):
    def __init__(self):
        self.stack = []
        self.current_nesting_level = 0
        self.add_symtab(self.current_nesting_level)
        self.program_id = None

    def set_program_id(self, pid):
        self.program_id = pid

    def get_program_id(self):
        return self.program_id

    def get_current_nesting_level(self):
        return self.current_nesting_level

    def add_symtab(self, level):
        self.stack.append(SymTab(level))

    def get_local_symtab(self):
        return self.stack[self.current_nesting_level]

    def enter_local(self, name):
        return self.stack[self.current_nesting_level].enter(name)

    def lookup_local(self, name):
        return self.stack[self.current_nesting_level].lookup(name)

    def lookup(self, name):
        entry = None
        for i in range(self.current_nesting_level, 0, -1):
            entry = self.stack[i].lookup(name)
            if entry:
                break

        return entry

    def push(self, symtab):
        self.current_nesting_level += 1
        if symtab == None:
            symtab = SymTab(self.current_nesting_level)

        self.stack.append(symtab)
        return symtab

    def pop(self):
        symtab = self.stack[self.current_nesting_level]
        del self.stack[-1]
        self.current_nesting_level -= 1
        return symtab


class SymTab(SymTabIF):
    def __init__(self, nesting_level):
        self.nesting_level = nesting_level
        self.map = {}

    def get_nesting_level(self):
        return self.nesting_level

    def enter(self, name):
        entry = SymTabEntry(name, self)
        self.map[name] = entry
        return entry

    def lookup(self, name):
        return self.map.get(name)

    def get_sorted_entries(self):
        l = list(self.map.values())
        l.sort(key=lambda x:x.name)
        return l


class SymTabEntry(SynTabEntryIF):
    def __init__(self, name, symtab):
        self.name = name
        self.symtab = symtab
        self.line_numbers = []
        self.attribute = {}

        print('Entry name = ', self.name, " ", self)

    def get_line_numbers(self):
        return self.line_numbers

    def get_name(self):
        return self.name

    def get_symtab(self):
        return self.symtab

    def append_line_number(self, num):
        self.line_numbers.append(num)

    def set_attribute(self, key, value):
        self.attribute[key] = value

    def get_attribute(self, key):
        return self.attribute[key]

