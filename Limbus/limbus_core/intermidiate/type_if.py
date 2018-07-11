# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class TypeSpecIF(metaclass=ABCMeta):
    @abstractmethod
    def get_form(self):
        raise NotImplementedError()

    @abstractmethod
    def set_identifier(self, identifier):
        raise NotImplementedError()

    @abstractmethod
    def get_identifier(self):
        raise NotImplementedError()

    @abstractmethod
    def set_attribute(self, key, value):
        raise NotImplementedError()

    @abstractmethod
    def get_attribute(self, key):
        raise NotImplementedError()

    @abstractmethod
    def is_pascal_string(self):
        raise NotImplementedError()

    @abstractmethod
    def base_type(self):
        raise NotImplementedError()

class TypeFormIF(metaclass=ABCMeta):
    pass

class TypeKeyIF(metaclass=ABCMeta):
    pass

