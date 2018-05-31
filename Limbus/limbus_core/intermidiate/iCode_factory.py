# -*- coding: utf-8 -*-
from .iCode_impl import iCode, iCodeNode


class iCodeFactory:
    def create(self):
        return iCode()


class iCodeNodeFactory:
    def create(self, type):
        return iCodeNode(type)
