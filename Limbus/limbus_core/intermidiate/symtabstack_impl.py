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
        return self.lookup_local(name)


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

