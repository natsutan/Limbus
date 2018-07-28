import sys
import copy

from limbus_core.frontend.parser import Parser
from limbus_core.intermidiate.iCode_factory import iCodeFactory, iCodeNodeFactory
from limbus_core.intermidiate.iCode_if import iCodeNodeType
from limbus_core.intermidiate.type_impl import Predefined, Definition, TypeSpec, TypeForm
from limbus_core.intermidiate.type_checker import TypeChecker

from ..limbus_core.frontend.token import Token
from ..limbus_core.intermidiate.symtabstack_impl import SymTabEntry
from ..limbus_core.intermidiate.iCode_impl import iCodeNode
from ..pascal.pascal_parser import ExpressionParser
from ..pascal.pascal_token import PascalSpecialSymbol, PascalWordToken

from pascal.pascal_parser import StatementParser, ExpressionParser, DeclarationsParser

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

    def parse_actual_parameters(self, token: PascalWordToken, pfid: SymTabEntry, is_declared: bool, is_read: bool,
                                is_write: bool):
        """

        :type is_write: bool
        """
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

                # Optional Precision
                token = self.current_token()
                actual_node.add_child(self.parse_write_spec(token))

            prms_node.add_child(actual_node)
            token = self.synchronize(self.COMMA_SET, ptt_set=self.COMMA_SET_PTT)

            if token.value == 'COMMA':
                token = self.next_token()
            elif token.value in ExpressionParser.EXPR_START_SET:
                self.error_handler.flag(token, 'MISSING_COMMA', self)
            elif token.value == 'RIGHT_PAREN':
                token = self.synchronize(ExpressionParser.EXPR_START_SET, ptt_set=ExpressionParser.EXPR_START_SET_PTT)

        token = self.next_token()
        if len(prms_node.get_children()) == 0 or (is_declared and prms_index != prms_cnt - 1):
            self.error_handler.flag(token, 'WRONG_NUMBER_OF_PARMS', self)

        return prms_node

    def check_actual_parameter(self, token: PascalWordToken, formal_id: SymTabEntry, actual_node: iCodeNode):
        formal_defn: Definition = formal_id.get_definition()
        formal_type: TypeSpec = formal_id.get_typespec()
        actual_type: TypeSpec = actual_node.get_typespec()

        if formal_defn == Definition.VAR_PARM:
            if actual_node.get_type() != iCodeNodeType.VARIABLE or actual_type != formal_type:
                self.error_handler.flag(token, 'INVALID_VAR_PARM', self)
        elif not TypeChecker().are_assignment_compatible(formal_type, actual_type):
            self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

    def parse_write_spec(self, token: PascalWordToken):
        if token.value == 'COLON':
            token = self.next_token()
            expression_parser: ExpressionParser = ExpressionParser(self)
            spec_node: iCodeNode = expression_parser.parse(token)
            if spec_node.get_type() == iCodeNodeType.STRING_CONSTANT:
                return spec_node
            else:
                self.error_handler.flag(token, 'INVALID_NUMBER', self)
                return None
        else:
            return None


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


class CallStandardParser(CallParser):

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        call_node: iCodeNode = iCodeNodeFactory().create('CALL')
        name: str = token.value.lower()
        pfid: SymTabEntry = Parser.symtab_stack.lookup(name)
        routine_code: str = pfid.get_attribute('ROUTINE_CODE')

        call_node.set_attribute('ID', pfid)
        token = self.next_token()

        if routine_code == 'READ' or routine_code == 'READLN':
            return self.parse_read_readln(token, call_node, pfid)
        elif routine_code == 'WRITE' or routine_code == 'WRITELN':
            return self.parse_write_writeln(token, call_node, pfid)
        elif routine_code == 'EOF' or routine_code == 'EOLN':
            return self.parse_eof_eoln(token, call_node, pfid)
        elif routine_code == 'ABS' or routine_code == 'SQR':
            return self.parse_abs_sqr(token, call_node, pfid)
        elif routine_code in ['ARCTAN', 'COS', 'EXP', 'LN', 'SIN', 'SQRT']:
            return self.parse_arctan_cos_exp_ln_sin_sqrt(token, call_node, pfid)
        elif routine_code == 'PRED' or routine_code == 'SUCC':
            return self.parse_pred_succ(token, call_node, pfid)
        elif routine_code == 'CHR':
            return self.parse_chr(token, call_node, pfid)
        elif routine_code == 'ODD':
            return self.parse_odd(token, call_node, pfid)
        elif routine_code == 'ORD':
            return self.parse_ord(token, call_node, pfid)
        elif routine_code == 'ROUND' or routine_code == 'TRUNC':
            return self.parse_round_trunc(token, call_node, pfid)
        else:
            return None

    def parse_read_readln(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, True, False)
        call_node.add_child(prms_node)

        if pfid == Predefined.readln_id and len(call_node.get_children()) == 0:
            self.error_handler.flag(token, 'WRONG_NUMBER_OF_PARMS', self)

        return call_node

    def parse_write_writeln(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, True)
        call_node.add_child(prms_node)

        if pfid == Predefined.writeln_id and len(call_node.get_children()) == 0:
            self.error_handler.flag(token, 'WRONG_NUMBER_OF_PARMS', self)

        return call_node

    def parse_eof_eoln(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, False)
        call_node.add_child(prms_node)

        if check_parm_count(token, prms_node, 0):
            call_node.set_typespec(Predefined.boolean_type)

        return call_node

    def parse_abs_sqr(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, False)
        call_node.add_child(prms_node)

        if check_parm_count(token, prms_node, 1):
            arg_type: TypeSpec = prms_node.get_children()[0].get_typespec().base_type()

            if arg_type == Predefined.integer_type or arg_type == Predefined.real_type:
                call_node.set_typespec(arg_type)
            else:
                self.error_handler.flag(token, 'INVALID_TYPE', self)

        return call_node

    def parse_arctan_cos_exp_ln_sin_sqrt(self, token, call_node, pfid) -> object:
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, False)
        call_node.add_child(prms_node)

        if check_parm_count(token, prms_node, 1):
            arg_type: TypeSpec = prms_node.get_children()[0].get_typespec().base_type()

            if arg_type == Predefined.integer_type or arg_type == Predefined.real_type:
                call_node.set_typespec(Predefined.integer_type)
            else:
                self.error_handler.flag(token, 'INVALID_TYPE', self)

        return call_node

    def parse_pred_succ(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, False)
        call_node.add_child(prms_node)

        if check_parm_count(token, prms_node, 1):
            arg_type: TypeSpec = prms_node.get_children()[0].get_typespec().base_type()
            if arg_type == Predefined.integer_type or arg_type.get_form() == TypeForm.ENUMERATION:
                call_node.set_typespec(arg_type)
            else:
                self.error_handler.flag(token, 'INVALID_TYPE', self)

        return call_node

    def parse_chr(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, False)
        call_node.add_child(prms_node)

        if check_parm_count(token, prms_node, 1):
            arg_type: TypeSpec = prms_node.get_children()[0].get_typespec().base_type()
            if arg_type == Predefined.integer_type:
                call_node.set_typespec(Predefined.char_type)
            else:
                self.error_handler.flag(token, 'INVALID_TYPE', self)

        return call_node

    def parse_odd(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, False)
        call_node.add_child(prms_node)

        if check_parm_count(token, prms_node, 1):
            arg_type: TypeSpec = prms_node.get_children()[0].get_typespec().base_type()
            if arg_type == Predefined.integer_type:
                call_node.set_typespec(Predefined.boolean_type)
            else:
                self.error_handler.flag(token, 'INVALID_TYPE', self)

        return call_node

    def parse_ord(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, False)
        call_node.add_child(prms_node)

        if check_parm_count(token, prms_node, 1):
            arg_type: TypeSpec = prms_node.get_children()[0].get_typespec().base_type()
            if arg_type == Predefined.char_type or arg_type.get_form() == TypeForm.ENUMERATION:
                call_node.set_typespec(Predefined.integer_type)
            else:
                self.error_handler.flag(token, 'INVALID_TYPE', self)

        return call_node

    def parse_round_trunc(self, token, call_node, pfid):
        prms_node: iCodeNode = self.parse_actual_parameters(token, pfid, False, False, False)
        call_node.add_child(prms_node)

        if check_parm_count(token, prms_node, 1):
            arg_type: TypeSpec = prms_node.get_children()[0].get_typespec().base_type()
            if arg_type == Predefined.real_type:
                call_node.set_typespec(Predefined.integer_type)
            else:
                self.error_handler.flag(token, 'INVALID_TYPE', self)

        return call_node


def check_parm_count(token, prms_node, count):
    if ((not prms_node) and count == 0) or len(prms_node.get_children()) == count:
        return True
    else:
        return False


class DeclaredRoutineParser(DeclarationsParser):

    def __init__(self, parent):
        self.dummy_counter = 0
        super().__init__(parent)

    def parse(self, token, parent_id: SymTabEntry):
        routine_defn: Definition = None
        dummy_name: str = None
        routine_id: SymTabEntry = None
        routine_type = token.type

        if routine_type == 'PROGRAM':
            token = self.next_token()
            routine_defn = Definition.PROGRAM
            dummy_name = 'DummyProgramName'.lower()
        elif routine_defn == 'PROCEDURE':
            token = self.next_token()
            routine_defn = Definition.PROCEDURE
            self.dummy_counter += 1
            dummy_name = 'DummyFunctionName_'.lower() + "%03d" % self.dummy_counter
        else:
            routine_defn = Definition.PROGRAM
            dummy_name = 'DummyProgramName'.lower()

        







