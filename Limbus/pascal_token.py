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
        super().__init__(source)


class PascalNumberToken(Token):
    def __init__(self, source):
        super().__init__(source)


class PascalStringToken(Token):
    def __init__(self, source):
        super().__init__(source)


class  PascalSpecialToken(Token):
    def __init__(self, source):
        super().__init__(source)
