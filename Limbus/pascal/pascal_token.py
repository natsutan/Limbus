# -*- coding: utf-8 -*-
import math
from enum import Enum,  auto
from limbus_core.frontend.token import Token, TokenType


class PTT(Enum):
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
            self.ptype = PTT.RESERVED
            self.value = s.upper()
        else:
            self.ptype = PTT.IDENTIFIER
            self.value = s


class PascalNumberToken(Token):
    MAX_EXPONENT = 37

    def __init__(self, source):
        self.ptype = None
        self.value = None
        self.text = ""
        super().__init__(source)

    def extract(self):
        self.type = TokenType.PASCAL

        exponent_sign = '+'
        fraction_digits = None
        exponent_digits = None
        saw_dotdot = False
        self.text = ""

        self.ptype = PTT.INTEGER  # 仮
        whole_digits = self.unsigned_integer_digits()
        if self.type == TokenType.ERROR:
            return

        cc = self.current_char()
        if cc == '.':
            pc = self.peek_char()
            if pc == '.':
                saw_dotdot = True
            else:
                self.ptype = PTT.REAL
                self.text = self.text + cc
                cc = self.next_char()
                fraction_digits = self.unsigned_integer_digits()
                if self.type == TokenType.ERROR:
                    return
        cc = self.current_char()
        if (not saw_dotdot) and (cc == 'e' or cc == 'E'):
            self.ptype = PTT.REAL
            self.text = self.text + cc
            cc = self.next_char()

            if cc == '+' or cc == '-':
                self.text = self.text + cc
                exponent_sign = cc
                cc = self.next_char()

            exponent_digits = self.unsigned_integer_digits()

        if self.ptype == PTT.INTEGER:
            self.value = int(whole_digits)
        elif self.ptype == PTT.REAL:
            fv = self.compute_float_value(whole_digits, fraction_digits, exponent_digits, exponent_sign)
            if self.type != TokenType.ERROR:
                  self.value = float(fv)



    def unsigned_integer_digits(self):
        cc = self.current_char()
        if not cc.isdigit():
            self.type = TokenType.ERROR
            self.value = 'INVALID_NUMBER'
            return None

        digits = ''
        while cc.isdigit():
            self.text = self.text + cc
            digits = digits + cc
            cc = self.next_char()

        return digits

    def compute_float_value(self, whole_digits, fraction_digits, exponent_digits, exponent_sign):
        fv = 0.0
        if exponent_digits == None:
            exponentical_value = 0
        else:
            exponentical_value = int(exponent_digits)
        digits = whole_digits

        if exponent_sign == '-':
            exponentical_value = -exponentical_value

        if fraction_digits != None:
            exponentical_value = exponentical_value - len(fraction_digits)
            digits = digits + fraction_digits

        if abs(exponentical_value + len(whole_digits)) > PascalNumberToken.MAX_EXPONENT:
            self.type = TokenType.ERROR
            self.value = 'RANGE_REAL'
            return 0.0

        index = 0
        while index < len(digits):
            fv = 10 * fv + int(digits[index])
            index = index + 1

        if exponentical_value != 0:
            fv = fv * math.pow(10, exponentical_value)

        return fv


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
            self.ptype = PTT.STRING
            self.value = value
        else:
            self.type = TokenType.ERROR
            self.value = "UNEXPECTED_EOF"

        self.text = str(text)


class PascalSpecialToken(Token):

    single_chars = "+-*/,;'=(){}^[]"

    def __init__(self, source):
        self.ptype = None
        super().__init__(source)
        self.type = TokenType.PASCAL

    def extract(self):
        cc = self.current_char()
        text = cc
        if cc in self.single_chars:
            self.next_char()
        elif cc == ':':
            cc = self.next_char()
            if cc == '=':
                text = text + cc
                self.next_char()
        elif cc == '<':
            cc = self.next_char()
            if cc == '=':
                text = text + cc
                self.next_char()
            elif cc == '>':
                text = text + cc
                self.next_char()
        elif cc == '>':
            cc = self.next_char()
            if cc == '=':
                text = text + cc
                self.next_char()
        elif cc == '.':
            cc = self.next_char()
            if cc == '.':
                text = text + cc
                self.next_char()
        else:
            self.next_char()
            self.type = TokenType.ERROR
            self.value = 'INVALID CHAR'
            return

        self.text = text
        self.ptype = special_symbols[text]
        self.value = str(self.ptype).split('.')[1]

