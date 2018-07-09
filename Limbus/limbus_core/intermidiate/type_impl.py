# -*- coding: utf-8 -*-

from enum import Enum,  auto
from .type_if import TypeFormIF, TypeKeyIF, TypeSpecIF
from .symtabstack_impl import SymTabKey


class TypeForm(TypeFormIF):
    SCALAR = 0
    ENUMERATION = 1
    SUBRANGE = 2
    ARRAY = 3
    RECORD = 4


class TypeKey(TypeKeyIF):
    ENUMERATION_CONSTANTS = 0
    SUBRANGE_BASE_TYPE = 1
    SUBRANGE_MIN_VALUE = 2
    SUBRANGE_MAX_VALUE = 3
    ARRAY_INDEX_TYPE = 4
    ARRAY_ELEMENT_TYPE = 5
    ARRAY_ELEMENT_COUNT = 6
    RECORD_SYMTAB = 7


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

    def __init__(self, text):
        if isinstance(text, str):
            self.text = text
        else:
            self.text = str(text)

    def get_text(self):
        return self.text


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

        Predefined.real_id = symtab_stack.enter_local("real")
        Predefined.real_type = TypeSpec(TypeForm.SCALAR)
        Predefined.real_type.set_identifier(Predefined.real_id)
        Predefined.real_id.set_definition(Definition.TYPE)
        Predefined.real_id.set_typespec(Predefined.real_type)

        Predefined.boolean_id = symtab_stack.enter_local("boolean")
        Predefined.boolean_type = TypeSpec(TypeForm.ENUMERATION)
        Predefined.boolean_type.set_identifier(Predefined.boolean_id)
        Predefined.boolean_id.set_definition(Definition.TYPE)
        Predefined.boolean_id.set_typespec(Predefined.boolean_type)

        Predefined.char_id = symtab_stack.enter_local("char")
        Predefined.char_type = TypeSpec(TypeForm.SCALAR)
        Predefined.char_type.set_identifier(Predefined.char_id)
        Predefined.char_id.set_definition(Definition.TYPE)
        Predefined.char_id.set_typespec(Predefined.char_type)

        Predefined.undefined_type = TypeSpec(TypeForm.SCALAR)

    def initialize_constants(self, symtab_stack):
        Predefined.false_id = symtab_stack.enter_local('false')
        Predefined.false_id.set_definition(Definition.ENUMERATION_CONSTANT)
        Predefined.false_id.set_typespec(Predefined.boolean_type)
        Predefined.false_id.set_attribute('CONSTANT_VALUE', 0)

        Predefined.true_id = symtab_stack.enter_local('true')
        Predefined.true_id.set_definition(Definition.ENUMERATION_CONSTANT)
        Predefined.true_id.set_typespec(Predefined.boolean_type)
        Predefined.true_id.set_attribute('CONSTANT_VALUE', 1)

        constants = [Predefined.false_id, Predefined.true_id]
        Predefined.boolean_type.set_attribute(Definition.ENUMERATION_CONSTANT, constants)


class TypeSpec(TypeSpecIF):
    def __init__(self, value):
        if not(type(value) is TypeForm):
            self.form = value
            self.identifier = None
            self.attributes = {}
        else:
            self.form = TypeForm.ARRAY
            index_type = TypeSpec(TypeForm.SUBRANGE)
            index_type.set_attribute(TypeKey.SUBRANGE_BASE_TYPE, Predefined.integer_type)
            index_type.set_attribute(TypeKey.SUBRANGE_MIN_VALUE, 1)
            index_type.set_attribute(TypeKey.SUBRANGE_MAX_VALUE, len(value))

            self.set_attribute(TypeKey.ARRAY_INDEX_TYPE, index_type)
            self.set_attribute(TypeKey.ARRAY_ELEMENT_TYPE, Predefined.char_type)
            self.set_attribute(TypeKey.ARRAY_ELEMENT_COUNT, len(value))

    def get_form(self):
        return self.form

    def set_identifier(self, identifier):
        self.identifier = identifier

    def get_identifier(self):
        return self.identifier

    def set_attribute(self, key, value):
        self.attributes[key] = value

    def get_attribute(self, key):
        if key in self.attributes:
            return self.attributes[key]
        else:
            return None

    def is_pascal_string(self):
        if self.form == TypeForm.ARRAY:
            elem_type = self.get_attribute(TypeKey.ARRAY_ELEMENT_TYPE)
            index_type = self.get_attribute(TypeKey.ARRAY_INDEX_TYPE)
            return elem_type == Predefined.char_type and index_type == Predefined.integer_type
        else:
            return False

    def base_type(self):
        if self.form == TypeForm.SUBRANGE:
            return self.get_attribute(TypeKey.SUBRANGE_BASE_TYPE)
        else:
            return self

