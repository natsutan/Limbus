# -*- coding: utf-8 -*-
import copy

from .iCode_if import *

class iCode(iCodeIF):
    def __init__(self):
        self.root = None

    def set_root(self, node):
        self.root = node
        return self.root


class iCodeNode(iCodeNodeIF):
    def __init__(self, ntype):
        self.type = ntype
        self.parent = None
        self.children = []
        self.attribute = {}

    def get_type(self):
        return self.type

    def get_parent(self):
        return self.parent

    def add_child(self, node):
        if node:
            self.children.append(node)
        return node

    def get_children(self):
        return self.children

    def set_attribute(self, key, value):
        self.attribute[key] = value

    def get_attribute(self, key):
        return self.attribute[key]

    def copy(self):
        return copy.deepcopy(self)

    def __str__ (self):
        return str(self.type)

