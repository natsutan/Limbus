# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from enum import Enum,  auto


class iCodeNodeType(Enum):
    PROGRAM = auto() 
    PROCEDURE = auto()
    FUNCTION = auto() 
    COMPOUND = auto() 
    ASSIGN = auto() 
    LOOP = auto() 
    TEST = auto() 
    CALL = auto() 
    PARAMETERS = auto() 
    IF = auto() 
    SELECT = auto() 
    SELECT_BRANCH = auto() 
    SELECT_CONSTANTS = auto() 
    NO_OP = auto() 
    EQ = auto() 
    NE = auto() 
    LT = auto()
    LE = auto() 
    GT = auto() 
    GE = auto() 
    NOT = auto()
    ADD = auto() 
    SUBTRACT = auto() 
    OR = auto() 
    NEGATE = auto()
    MULTIPLY = auto()
    INTEGER_DIVIDE = auto() 
    FLOAT_DIVIDE = auto() 
    MOD = auto() 
    AND = auto()
    VARIABLE = auto() 
    SUBSCRIPTS = auto() 
    FIELD = auto() 
    INTEGER_CONSTANT = auto() 
    REAL_CONSTANT = auto() 
    STRING_CONSTANT = auto() 
    BOOLEAN_CONSTANT = auto()


class iCodeKey(Enum):
    LINE = auto()
    ID = auto()
    VALUE = auto()


class iCodeIF(metaclass=ABCMeta):
    @abstractmethod
    def set_root(self, node):
        raise NotImplementedError()

    @abstractmethod
    def get_root(self, node):
        raise NotImplementedError()


class iCodeNodeIF(metaclass=ABCMeta):
    @abstractmethod
    def get_type(self):
        raise NotImplementedError()

    @abstractmethod
    def get_parent(self):
        raise NotImplementedError()

    @abstractmethod
    def add_child(self, node):
        raise NotImplementedError()

    @abstractmethod
    def get_children(self):
        raise NotImplementedError()

    @abstractmethod
    def set_attribute(self, key, value):
        raise NotImplementedError()

    @abstractmethod
    def get_attribute(self, key):
        raise NotImplementedError()

    @abstractmethod
    def copy(self):
        raise NotImplementedError()


