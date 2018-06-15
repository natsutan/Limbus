# -*- coding: utf-8 -*-

from enum import Enum,  auto
from .type_if import TypeFormIF, TypeKeyIF, TypeSpecIF

class TypeForm(Enum, TypeFormIF):
    CALAR = auto()
    ENUMERATION = auto()
    SUBRANGE = auto()
    ARRAY = auto()
    RECORD = auto()

class TypeKey(Enum, TypeKeyIF):
    ENUMERATION_CONSTANTS = auto()
    SUBRANGE_BASE_TYPE = auto()
    SUBRANGE_MIN_VALUE = auto()
    SUBRANGE_MAX_VALUE = auto()
    ARRAY_INDEX_TYPE = auto()
    ARRAY_ELEMENT_TYPE = auto()
    ARRAY_ELEMENT_COUNT = auto()
    RECORD_SYMTAB = auto()



class TypeSpec(TypeSpecIF):
    def __init__(self, form):
        self.form = form
        self.identifier  = None

    def get_form(self):
        raise NotImplementedError()

    def set_identifier(self, identifier):
        raise NotImplementedError()

    def get_identifier(self):
        raise NotImplementedError()

    def set_attribute(self, key, value):
        raise NotImplementedError()

    def get_attribute(self, key):
        raise NotImplementedError()

    def is_pascal_string(self):
        raise NotImplementedError()

    def base_type(self):
        raise NotImplementedError()

