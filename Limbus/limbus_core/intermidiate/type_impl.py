# -*- coding: utf-8 -*-

from enum import Enum,  auto
from .type_if import TypeFormIF, TypeKeyIF, TypeSpecIF


class TypeForm(Enum, TypeFormIF):
    SCALAR = auto()
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


class Definition(Enum):
    CONSTANT = auto()
    ENUMERATION_CONSTANT = auto()
    TYPE = auto()
    VARIABLE = auto()
    FIELD = auto()
    VALUE_PARM = auto()
    VAR_PARM = auto()
    PROGRAM_PARM = auto()
    PROGRAM = auto()
    PROCEDURE = auto()
    FUNCTION = auto()
    UNDEFINED = auto()


class Predefined:
    integer_type = None
    real_type = None
    boolean_type = None
    char_type = None
    undefined_type = None

    integer_id = None
    real_id = None
    boolean_id = None
    char_id = None
    false_id = None
    true_id = None

    def initialize(self, symtab_stack):
        self.initialize_types(symtab_stack)
        self.initialize_constants(symtab_stack)

    def initialize_types(self, symtab_stack):
        Predefined.integer_id = symtab_stack.enter_local("integer")
        Predefined.integer_type = TypeSpec(TypeForm.SCALAR)
        Predefined.integer_type.set_identifier(Predefined.integer_id)
        Predefined.integer_id.set_definition(Definition.TYPE)
        Predefined.integer_id.set_typespec(Predefined.integer_type)



class TypeSpec(TypeSpecIF):
    def __init__(self, value):
        if not(type('string') is str):
            self.form = value
            self.identifier = None
        else:
            self.form = TypeForm.ARRAY
            index_type = TypeSpec(TypeForm.SUBRANGE)
            index_type.set_attribute(TypeKey.SUBRANGE_BASE_TYPE, )



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

