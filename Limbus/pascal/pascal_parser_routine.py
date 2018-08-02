import sys
import copy

from limbus_core.frontend.parser import Parser
from limbus_core.intermidiate.iCode_factory import iCodeFactory, iCodeNodeFactory
from limbus_core.intermidiate.iCode_if import iCodeNodeType
from limbus_core.intermidiate.type_impl import Predefined, Definition, TypeSpec, TypeForm
from limbus_core.intermidiate.type_checker import TypeChecker

from limbus_core.frontend.token import Token
from limbus_core.intermidiate.symtabstack_impl import SymTabEntry, SymTab
from limbus_core.intermidiate.iCode_impl import iCodeNode
from pascal.pascal_token import PascalSpecialSymbol, PascalWordToken

from pascal.pascal_parser import StatementParser, ExpressionParser, DeclarationsParser, BlockParser, VariableDeclarationsParser

#import pascal.pascal_parser

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

    PARAMETER_SET = copy.deepcopy(DeclarationsParser.DECLARATION_START_SET)
    PARAMETER_SET = PARAMETER_SET + ['VAR', 'RIGHT_PAREN']
    PARAMETER_SET_PTT = [PTT.IDENTIFIER, ]

    LEFT_PAREN_SET = copy.deepcopy(DeclarationsParser.DECLARATION_START_SET)
    LEFT_PAREN_SET = LEFT_PAREN_SET + ['LEFT_PAREN', 'SEMICOLON', 'COLON']

    RIGHT_PAREN_SET = copy.deepcopy(DeclarationsParser.DECLARATION_START_SET)
    RIGHT_PAREN_SET = RIGHT_PAREN_SET + ['RIGHT_PAREN', 'SEMICOLON', 'COLON']

    PARAMETER_FOLLOW_SET = ['COLON', 'RIGHT_PAREN', 'SEMICOLON'] + \
                           copy.deepcopy(DeclarationsParser.DECLARATION_START_SET)
    COMMA_SET = ['COMMA', 'COLON', 'RIGHT_PAREN', 'SEMICOLON'] + copy.deepcopy(DeclarationsParser.DECLARATION_START_SET)
    COMMA_SET_PTT = [PTT.IDENTIFIER, ]

    def __init__(self, parent):
        self.dummy_counter = 0
        super().__init__(parent)

    def parse(self, token, parent_id: SymTabEntry) -> SymTabEntry:
        routine_defn: Definition = None
        routine_type = token.value

        if routine_type == 'PROGRAM':
            token = self.next_token()
            routine_defn = Definition.PROGRAM
            dummy_name = 'DummyProgramName'.lower()
        elif routine_type == 'PROCEDURE':
            token = self.next_token()
            routine_defn = Definition.PROCEDURE
            self.dummy_counter += 1
            dummy_name = 'DummyProcedureName_'.lower() + "%03d" % self.dummy_counter
        elif routine_type == 'FUNCTION':
            token = self.next_token()
            routine_defn = Definition.FUNCTION
            self.dummy_counter += 1
            dummy_name = 'DummyFunctionName_'.lower() + "%03d" % self.dummy_counter
        else:
            routine_defn = Definition.PROGRAM
            dummy_name = 'DummyProgramName'.lower()

        routine_id: SymTabEntry = self.parse_routine_name(token, dummy_name)
        routine_id.set_definition(routine_defn)

        token = self.current_token()
        icode = iCodeFactory().create()
        routine_id.set_attribute('ROUTINE_ICODE', icode)
        routine_id.set_attribute('ROUTINE_ROUTINES', [])

        if routine_id.get_attribute('ROUTINE_CODE') == 'FORWARD':
            symtab: SymTab = routine_id.get_attribute('ROUTINE_SYMTAB')
            Parser.symtab_stack.push(symtab)
        else:
            routine_id.set_attribute('ROUTINE_SYMTAB', Parser.symtab_stack.push(None))

        if routine_defn == Definition.PROGRAM:
            Parser.symtab_stack.set_program_id(routine_id)
        elif routine_id.get_attribute('ROUTINE_CODE' != 'FORWARD'):
            subroutines = parent_id.get_attribute('ROUTINE_ROUTINES')
            subroutines.add(routine_id)

        if routine_id.get_attribute('ROUTINE_CODE') == 'FORWARD':
            if token.value != 'SEMICOLON':
                self.error_handler.flag(token, 'ALREADY_FORWARDED', self)
                self.parse_header(token, routine_id)
        else:
            self.parse_header(token, routine_id)

        token = self.current_token()
        if token.value == 'SEMICOLON':
            token = self.next_token()
            while token.value == 'SEMICOLON':
                token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_SEMICOLON', self)

        if token.ptype == PTT.IDENTIFIER and token.value.lower() == 'forward':
            token = self.next_token()
            routine_id.set_attribute('ROUTINE_CODE', 'FORWARD')
        else:
            routine_id.set_attribute('ROUTINE_CODE', 'DECLARED')
            block_parser: BlockParser = BlockParser(self)
            root_node: iCodeNode = block_parser.parse(token, routine_id)
            Parser.iCode.set_root(root_node)

        Parser.symtab_stack.pop()
        return routine_id

    def parse_routine_name(self, token, dummy_name: str) -> SymTabEntry:
        if token.ptype == PTT.IDENTIFIER:
            routine_name: str = token.value.lower()
            routine_id: SymTabEntry = Parser.symtab_stack.lookup_local(routine_name)

            if not routine_id:
                routine_id = Parser.symtab_stack.enter_local(routine_name)
            elif routine_id.get_attribute('ROUTINE_CODE') != 'FORWARD':
                routine_id = None
                self.error_handler.flag(token, 'IDENTIFIER_REDEFINED', self)

            token = self.next_token()
        else:
            routine_id = None
            self.error_handler.flag(token, 'MISSING_IDENTIFIER', self)

        if not routine_id:
            routine_id = Parser.symtab_stack.enter_local(dummy_name)

        return routine_id

    def parse_header(self, token, routine_id: SymTabEntry):
        self.parse_formal_parameter(token, routine_id)
        token = self.current_token()

        if routine_id.get_definition() == Definition.FUNCTION:
            variable_decl_parser: VariableDeclarationsParser = VariableDeclarationsParser(self)
            variable_decl_parser.set_definition(Definition.FUNCTION)
            typespec: TypeSpec = variable_decl_parser.parse(token, self)
            token = self.current_token()

            if typespec:
                form: TypeForm = typespec.get_form()
                if form == TypeForm.ARRAY or form == TypeForm.RECORD:
                    self.error_handler.flag(token, 'INVALID_TYPE', self)
        else:
            typespec = Predefined.undefined_type

        routine_id.set_typespec(typespec)
        token = self.current_token()

    def parse_formal_parameter(self, token, routine_id: SymTabEntry):
        token = self.synchronize(self.LEFT_PAREN_SET)
        if token.value == 'LEFT_PAREN':
            token = self.next_token()
            prms: list = []
            token = self.synchronize(self.PARAMETER_SET, ptt_set=self.PARAMETER_SET_PTT)

            while token.ptype == PTT.IDENTIFIER or token.value == 'VAR':
                sublist = self.parse_prms_sublist(token, routine_id)
                prms = prms + sublist
                token = self.current_token()

            if token.value == 'RIGHT_PAREN':
                token = self.next_token()
            else:
                self.error_handler.flag(token, 'MISSING_RIGHT_PAREN', self)

            routine_id.set_attribute('ROUTINE_PARMS', prms)

    def parse_prms_sublist(self, token, routine_id):
        is_program: bool = routine_id.get_definition() == Definition.PROGRAM

        if is_program:
            prm_defn = Definition.PROGRAM_PARM
        else:
            prm_defn = None

        if token.value == 'VAR':
            if not is_program:
                prm_defn = Definition.VAR_PARM
            else:
                self.error_handler.flag(token, 'INVALID_VAR_PARM', self)
            token = self.next_token()
        elif not is_program:
            prm_defn = Definition.VAR_PARM

        variable_decl_parser: VariableDeclarationsParser = VariableDeclarationsParser(self)
        variable_decl_parser.set_definition(prm_defn)
        sublist = variable_decl_parser.parse_identifier_sublist(token, self.PARAMETER_FOLLOW_SET, self.COMMA_SET, ptt_set=self.COMMA_SET_PTT)
        token = self.current_token()

        if not is_program:
            if token.value == 'SEMICOLON':
                while token.value ==  'SEMICOLON':
                    token = self.next_token()
            elif token.value in VariableDeclarationsParser.NEXT_START_SET:
                self.parse_header(token, 'MISSING_SEMICOLON', self)

            token = self.synchronize(self.PARAMETER_SET, ptt_set=self.PARAMETER_SET_PTT)

        return sublist


class ProgramParser(DeclarationsParser):
    PROGRAM_START_SET = ['PROGRAM', 'SEMICOLON'] + DeclarationsParser.DECLARATION_START_SET

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token, parent_id: SymTabEntry):
        token = self.synchronize(self.PROGRAM_START_SET)

        routine_parser = DeclaredRoutineParser(self)
        routine_parser.parse(token, parent_id)

        token = self.current_token()
        if token.value != 'DOT':
            self.error_handler.flag(token, 'MISSING_PERIOD', self)

        return None



