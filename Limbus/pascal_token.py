# -*- coding: utf-8 -*-
from enum import Enum,  auto
from limbus_core.frontend.token import Token, TokenType

class PascalTokenType(Enum):
    DUMMY = auto()
    RESERVED = auto()
    SPECIAL_SYMBOL = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    REAL = auto()
    STRING = auto()


# reserved
reserved_list = ['AND', 'ARRAY', 'BEGIN', 'CASE', 'CONST', 'DIV', 'DO', 'DOWNTO', 'ELSE', 'END', 'FILE', 'FOR',
                 'FUNCTION', 'GOTO', 'IF', 'IN', 'LABEL', 'MOD', 'NIL', 'NOT', 'OF', 'OR', 'PACKED', 'PROCEDURE',
                 'PROGRAM', 'RECORD', 'REPEAT', 'SET', 'THEN', 'TO', 'TYPE', 'UNTIL', 'VAR', 'WHILE', 'WITH']


class PascalSpecialSymbol(Enum):
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    COLON_EQUALS = auto()
    DOT = auto()
    COMMA = auto()
    SEMICOLON = auto()
    COLON = auto()
    QUOTE = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    LESS_EQUALS = auto()
    GREATER_EQUALS = auto()
    GREATER_THAN = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    UP_ARROW = auto()
    DOT_DOT = auto()


special_symbols = {
    '+' : PascalSpecialSymbol.PLUS,
    '-' : PascalSpecialSymbol.MINUS,
    '*' : PascalSpecialSymbol.STAR,
    '/' : PascalSpecialSymbol.SLASH,
    ':=' : PascalSpecialSymbol.COLON_EQUALS,
    '.' : PascalSpecialSymbol.DOT,
    ',' : PascalSpecialSymbol.COMMA,
    ';' : PascalSpecialSymbol.SEMICOLON,
    ':' : PascalSpecialSymbol.COLON,
    "'" : PascalSpecialSymbol.QUOTE,
    '=' : PascalSpecialSymbol.EQUALS,
    '<>' : PascalSpecialSymbol.NOT_EQUALS,
    '<' : PascalSpecialSymbol.LESS_THAN,
    '<=' : PascalSpecialSymbol.LESS_EQUALS,
    '>=' : PascalSpecialSymbol.GREATER_EQUALS,
    '>' : PascalSpecialSymbol.GREATER_THAN,
    '(' : PascalSpecialSymbol.LEFT_PAREN,
    ')' : PascalSpecialSymbol.RIGHT_PAREN,
    '[' : PascalSpecialSymbol.LEFT_BRACKET,
    ']' : PascalSpecialSymbol.RIGHT_BRACKET,
    '{' : PascalSpecialSymbol.LEFT_BRACE,
    '}' : PascalSpecialSymbol.RIGHT_BRACE,
    '^' : PascalSpecialSymbol.UP_ARROW,
    '..' : PascalSpecialSymbol.DOT_DOT,
}


class PascalWordToken(Token):
    def __init__(self, source):
        self.ptype = None
        super().__init__(source)
        self.type = TokenType.PASCAL

    def extract(self):
        s = ""
        cc = self.current_char()
        while cc.isalpha() or cc.isdigit():
            s = s + cc
            cc = self.next_char()
            if not cc:
                break

        if s.upper() in reserved_list:
            self.ptype = PascalTokenType.RESERVED
            self.value = s.upper()
        else:
            self.ptype = PascalTokenType.IDENTIFIER
            self.value = s


class PascalNumberToken(Token):
    def __init__(self, source):
        super().__init__(source)


class PascalStringToken(Token):
    def __init__(self, source):
        self.ptype = None
        super().__init__(source)
        self.type = TokenType.PASCAL

    def extract(self):
        value = ""
        cc = self.next_char()
        text = "'"
        # EOF時、ccはNone
        # do while
        while True:
            if cc != "'" and cc != None:
                text = text + cc
                value = value + cc
                cc = self.next_char()

            if cc == "'":
                pc = self.peek_char()
                while cc == "'" and pc == "'":
                    text = text + "''"
                    value = value + "'"
                    cc = self.next_char()
                    cc = self.next_char()
                    pc = self.peek_char()

            if cc == "'" or not cc:
                break

        if cc == "'":
            self.next_char()
            text = text + "'"
            self.ptype = PascalTokenType.STRING
            self.value = value
        else:
            self.type = TokenType.ERROR
            self.value = "UNEXPECTED_EOF"

        self.text = str(text)


class  PascalSpecialToken(Token):
    def __init__(self, source):
        super().__init__(source)
