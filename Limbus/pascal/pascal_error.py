# -*- coding: utf-8 -*-

from enum import Enum,  auto


class PascalErrorType(Enum):
    ALREADY_FORWARDED = auto()
    CASE_CONSTANT_REUSED = auto()
    IDENTIFIER_REDEFINED = auto()
    IDENTIFIER_UNDEFINED = auto()
    INCOMPATIBLE_ASSIGNMENT = auto()
    INCOMPATIBLE_TYPES = auto()
    INVALID_ASSIGNMENT = auto()
    INVALID_CHARACTER = auto()
    INVALID_CONSTANT = auto()
    INVALID_EXPONENT = auto()
    INVALID_EXPRESSION = auto()
    INVALID_FIELD = auto()
    INVALID_FRACTION = auto()
    INVALID_IDENTIFIER_USAGE = auto()
    INVALID_INDEX_TYPE = auto()
    INVALID_NUMBER = auto()
    INVALID_STATEMENT = auto()
    INVALID_SUBRANGE_TYPE = auto()
    INVALID_TARGET = auto()
    INVALID_TYPE = auto()
    INVALID_VAR_PARM = auto()
    MIN_GT_MAX = auto()
    MISSING_BEGIN = auto()
    MISSING_COLON = auto()
    MISSING_COLON_EQUALS = auto()
    MISSING_COMMA = auto()
    MISSING_CONSTANT = auto()
    MISSING_DO = auto()
    MISSING_DOT_DOT = auto()
    MISSING_END = auto()
    MISSING_EQUALS = auto()
    MISSING_FOR_CONTROL = auto()
    MISSING_IDENTIFIER = auto()
    MISSING_LEFT_BRACKET = auto()
    MISSING_OF = auto()
    MISSING_PERIOD = auto()
    MISSING_PROGRAM = auto()
    MISSING_RIGHT_BRACKET = auto()
    MISSING_RIGHT_PAREN = auto()
    MISSING_SEMICOLON = auto()
    MISSING_THEN = auto()
    MISSING_TO_DOWNTO = auto()
    MISSING_UNTIL = auto()
    MISSING_VARIABLE = auto()
    NOT_CONSTANT_IDENTIFIER = auto()
    NOT_RECORD_VARIABLE = auto()
    NOT_TYPE_IDENTIFIER = auto()
    RANGE_INTEGER = auto()
    RANGE_REAL = auto()
    STACK_OVERFLOW = auto()
    TOO_MANY_LEVELS = auto()
    TOO_MANY_SUBSCRIPTS = auto()
    UNEXPECTED_EOF = auto()
    UNEXPECTED_TOKEN = auto()
    UNIMPLEMENTED = auto()
    UNRECOGNIZABLE = auto()
    WRONG_NUMBER_OF_PARMS = auto()

    # Fatal errors
    IO_ERROR = -101
    TOO_MANY_ERRORS = -102


error_text = {
    PascalErrorType.ALREADY_FORWARDED : "Already specified in FORWARD",
    PascalErrorType.CASE_CONSTANT_REUSED : "CASE constant reused",
    PascalErrorType.IDENTIFIER_REDEFINED : "Redefined identifier",
    PascalErrorType.IDENTIFIER_UNDEFINED : "Undefined identifier",
    PascalErrorType.INCOMPATIBLE_ASSIGNMENT : "Incompatible assignment",
    PascalErrorType.INCOMPATIBLE_TYPES : "Incompatible types",
    PascalErrorType.INVALID_ASSIGNMENT : "Invalid assignment statement",
    PascalErrorType.INVALID_CHARACTER : "Invalid character",
    PascalErrorType.INVALID_CONSTANT : "Invalid constant",
    PascalErrorType.INVALID_EXPONENT : "Invalid exponent",
    PascalErrorType.INVALID_EXPRESSION : "Invalid expression",
    PascalErrorType.INVALID_FIELD : "Invalid field",
    PascalErrorType.INVALID_FRACTION : "Invalid fraction",
    PascalErrorType.INVALID_IDENTIFIER_USAGE : "Invalid identifier usage",
    PascalErrorType.INVALID_INDEX_TYPE : "Invalid index type",
    PascalErrorType.INVALID_NUMBER : "Invalid number",
    PascalErrorType.INVALID_STATEMENT : "Invalid statement",
    PascalErrorType.INVALID_SUBRANGE_TYPE : "Invalid subrange type",
    PascalErrorType.INVALID_TARGET : "Invalid assignment target",
    PascalErrorType.INVALID_TYPE : "Invalid type",
    PascalErrorType.INVALID_VAR_PARM : "Invalid VAR parameter",
    PascalErrorType.MIN_GT_MAX : "Min limit greater than max limit",
    PascalErrorType.MISSING_BEGIN : "Missing BEGIN",
    PascalErrorType.MISSING_COLON : "Missing :",
    PascalErrorType.MISSING_COLON_EQUALS : "Missing :=",
    PascalErrorType.MISSING_COMMA : "Missing ,",
    PascalErrorType.MISSING_CONSTANT : "Missing constant",
    PascalErrorType.MISSING_DO : "Missing DO",
    PascalErrorType.MISSING_DOT_DOT : "Missing ..",
    PascalErrorType.MISSING_END : "Missing END",
    PascalErrorType.MISSING_EQUALS : "Missing =",
    PascalErrorType.MISSING_FOR_CONTROL : "Invalid FOR control variable",
    PascalErrorType.MISSING_IDENTIFIER : "Missing identifier",
    PascalErrorType.MISSING_LEFT_BRACKET : "Missing [",
    PascalErrorType.MISSING_OF : "Missing OF",
    PascalErrorType.MISSING_PERIOD : "Missing .",
    PascalErrorType.MISSING_PROGRAM : "Missing PROGRAM",
    PascalErrorType.MISSING_RIGHT_BRACKET : "Missing ]",
    PascalErrorType.MISSING_RIGHT_PAREN : "Missing ",
    PascalErrorType.MISSING_SEMICOLON : "Missing ;",
    PascalErrorType.MISSING_THEN : "Missing THEN",
    PascalErrorType.MISSING_TO_DOWNTO : "Missing TO or DOWNTO",
    PascalErrorType.MISSING_UNTIL : "Missing UNTIL",
    PascalErrorType.MISSING_VARIABLE : "Missing variable",
    PascalErrorType.NOT_CONSTANT_IDENTIFIER : "Not a constant identifier",
    PascalErrorType.NOT_RECORD_VARIABLE : "Not a record variable",
    PascalErrorType.NOT_TYPE_IDENTIFIER : "Not a type identifier",
    PascalErrorType.RANGE_INTEGER : "Integer literal out of range",
    PascalErrorType.RANGE_REAL : "Real literal out of range",
    PascalErrorType.STACK_OVERFLOW : "Stack overflow",
    PascalErrorType.TOO_MANY_LEVELS : "Nesting level too deep",
    PascalErrorType.TOO_MANY_SUBSCRIPTS : "Too many subscripts",
    PascalErrorType.UNEXPECTED_EOF : "Unexpected end of file",
    PascalErrorType.UNEXPECTED_TOKEN : "Unexpected token",
    PascalErrorType.UNIMPLEMENTED : "Unimplemented feature",
    PascalErrorType.UNRECOGNIZABLE : "Unrecognizable input",
    PascalErrorType.WRONG_NUMBER_OF_PARMS : "Wrong number of actual parameters",
    PascalErrorType.IO_ERROR : "Object I/O error",
    PascalErrorType.TOO_MANY_ERRORS : "Too many syntax errors"
}


class PascalError:
    def __init__(self, etype, message):
        self.type = etype
        self.message = message
        self.error_text = error_text[etype]

    def get_status(self):
        return int(self.type)

    def get_message(self):
        return self.message

