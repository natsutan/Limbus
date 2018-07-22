import sys
import copy

from limbus_core.message import Message, MessageType ,MessageListener
from limbus_core.frontend.parser import Parser
from limbus_core.intermidiate.iCode_factory import iCodeFactory, iCodeNodeFactory
from limbus_core.intermidiate.iCode_if import iCodeNodeType
from limbus_core.intermidiate.type_impl import Predefined, Definition, TypeSpec, TypeForm
from limbus_core.intermidiate.symtabstack_impl import SymTabKey
from limbus_core.intermidiate.type_checker import TypeChecker

from ..limbus_core.frontend.token import Token
from ..limbus_core.intermidiate.symtabstack_impl import SymTabEntry
from ..limbus_core.intermidiate.iCode_impl import iCodeNode
from ..pascal.pascal_parser import ExpressionParser
from ..pascal.pascal_token import PascalSpecialSymbol, PascalWordToken

from pascal.pascal_error import PascalErrorType, PascalError
from pascal.pascal_parser import StatementParser, ExpressionParser

from pascal.pascal_token import *
from pascal.pascal_parser import *


class CallParser(StatementParser):
    COMMA_SET = copy.deepcopy(ExpressionParser.EXPR_START_SET)
    COMMA_SET_PTT = copy.deepcopy(ExpressionParser.EXPR_START_SET_PTT)
    COMMA_SET.append('COMMA')
    COMMA_SET.append('RIGHT_PAREN')

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token:Token):
        name = token.value.lower()
        pfid = Parser.symtab_stack.lookup(name)
        routine_code = pfid.get_attribute('ROUTINE_CODE')

        if routine_code == 'DECLARED' or routine_code == 'FORWARD':
            call_parser = CallDeclaredParser(self)
        else:
            call_parser = CallStandardParser(self)

        return call_parser.parse(token)

    def parse_actual_parameters(self, token: PascalWordToken, pfid: SymTabEntry, is_declared: bool, is_read: bool, is_write: bool):
        expression_parser: ExpressionParser = ExpressionParser(self)
        prms_node: iCodeNode = iCodeFactory('PARAMETERS')
        formal_prms = []
        prms_cnt = 0
        prms_index = -1

        if is_declared:
            formal_prms = pfid.get_attribute('ROUTINE_PARMS')
            if formal_prms:
                prms_cnt = len(formal_prms)
            else:
                prms_cnt = 0

        if token.ptype == PascalSpecialSymbol.LEFT_PAREN:
            if prms_cnt != 0:
                self.error_handler.flag(token, 'WRONG_NUMBER_OF_PARMS', self)
            return None

        token: PascalWordToken = self.next_token()
        while token.ptype != PascalSpecialSymbol.RIGHT_PAREN:
            actual_node: iCodeNode = expression_parser.parse(token)
            if is_declared:
                prms_index += 1
                if prms_cnt < prms_cnt:
                    formal_id = formal_prms[prms_index]
                    self.set_actual_parameter(token, formal_id, actual_node)
                if prms_index == prms_cnt:
                    self.error_handler.flag(token, 'WRONG_NUMBER_OF_PARMS', self)
            elif is_read:
                typespec: TypeSpec = actual_node.get_typespec()
                form: TypeForm = typespec.get_form()
                if not (actual_node.get_type() == 'VARIABLE' and
                        (form == TypeForm.SCALAR or
                         typespec == Predefined.boolean_type or
                         (form == TypeForm.SUBRANGE and typespec.base_type() == Predefined.integer_type))):
                    self.error_handler.flag(token, 'INVALID_VAR_PARM', self)
            elif is_write:
                expr_node: iCodeNode = copy.deepcopy(actual_node)
                actual_node = iCodeNodeFactory().create('WRITE_PARM')
                actual_node.add_child(expr_node)

                typespec: TypeSpec = expr_node.get_typespec().base_type()
                form: TypeForm = typespec.get_form()

                if not (form == TypeForm.SCALAR or typespec == Predefined.boolean_type or typespec.is_pascal_string()):
                    self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

                # Optional field width
                token = self.current_token()
                actual_node.add_child(self.parse_write_spec(token))

                # Optional Presicision
                token = self.current_token()
                actual_node.add_child(self.parse_write_spec(token))

            prms_node.add_child(actual_node)
            token = self.synchronize(self.COMMA_SET, ptt_set=self.COMMA_SET_PTT)
            token_type = token.get_type()



        return ""


class CallDeclaredParser(CallParser):

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        call_node = iCodeFactory('CALL')
        name: str = token.value.lower()
        pfid = Parser.symtab_stack.lookup(name)
        call_node.set_attribute('ID', pfid)
        call_node.set_typespec(pfid.get_typespec())

        token = self.next_token()
        prms_node = self.parse_actual_parameters(token, pfid, True, False, True)
        call_node.add_child(prms_node)
        return call_node

