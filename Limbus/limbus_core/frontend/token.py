# -*- coding: utf-8 -*-
from enum import Enum,  auto


class TokenType(Enum):
    DUMMY = auto()
    EOF = auto()


class Token:
    def __init__(self, source):
        self.type = TokenType.DUMMY
        self.text = ""
        self.value = None
        self.source = source
        self.line_num = source.get_line_num()
        self.pos = source.get_position()

    def extract(self):
        self.text = self.current_char()
        self.value = 0
        self.next_char()

    def current_char(self):
        return self.source.current_char()

    def next_char(self):
        return self.source.next_char()

    def peek_char(self):
        return self.source.peek_char()





