# -*- coding: utf-8 -*-
from .iCode_impl import iCode


class iCodeFactory:
    def create(self):
        return iCode()
