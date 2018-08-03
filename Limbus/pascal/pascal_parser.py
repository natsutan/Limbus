# -*- coding: utf-8 -*-
import sys
import copy

from limbus_core.message import Message, MessageType ,MessageListener
from limbus_core.frontend.parser import Parser
from limbus_core.intermidiate.iCode_factory import iCodeFactory, iCodeNodeFactory
from limbus_core.intermidiate.iCode_if import iCodeNodeType
from limbus_core.intermidiate.type_impl import Predefined, Definition, TypeSpec, TypeForm
from limbus_core.intermidiate.symtabstack_impl import SymTabKey
from limbus_core.intermidiate.type_checker import TypeChecker

from pascal.pascal_error import PascalErrorType, PascalError
from pascal.pascal_token import *
from pascal.pascal_parser import *

class PascalErrorHandler:
    error_cnt = 0
    MAX_ERROR = 5

    def __init__(self):
        pass

    def flag(self, token, error_code, parser):
        line = parser.get_line()
        msg = Message(MessageType.SYNTAX_ERROR, (token, error_code, line))
        parser.send_message(msg)

        PascalErrorHandler.error_cnt = PascalErrorHandler.error_cnt + 1
        if PascalErrorHandler.error_cnt > PascalErrorHandler.MAX_ERROR:
            self.abort_translation('TOO_MANY_ERRORS', parser)

    def abort_translation(self, err_code, parser):
#        msg = Message(MessageType.SYNTAX_ERROR, "FATAL_ERROR:"+err_code)
        token = parser.current_token()
        line = parser.get_line()
        msg = Message(MessageType.SYNTAX_ERROR, (token, err_code, line))

        sys.exit(1)

    def get_error_count(self):
        return self.error_cnt


# -------------- Parser --------------------------
class PascalParserTD(Parser):
    def __init__(self, scanner):
        self.error_handler = PascalErrorHandler()
        self.routine_id = None
        self.predefined = Predefined()
        if isinstance(scanner, Parser):
            super().__init__(scanner.get_scanner())
        else:
            super().__init__(scanner)

    def get_routine_id(self):
        return self.routine_id

    def parse(self):
        from pascal.pascal_parser_routine import ProgramParser
        Predefined().initialize(Parser.symtab_stack)
        try:
            token = self.next_token()
            program_parser = ProgramParser(self)
            root_node = program_parser.parse(token, None)
            token = self.current_token()

            if root_node == None:
                self.error_handler.abort_translation('PARSE_ERROR', self)
                return


            # Parser.iCode.set_root(root_node)
            # Parser.symtab_stack.pop()
            #
            # token = self.current_token()
            # if token.ptype == PTT.RESERVED and token.value == 'DOT':
            #     self.error_handler.flag(token, 'MISSING_PERIOD', self)
            # token = self.current_token()
            #
            # line_number = token.line_num
            # err_cnt = self.get_error_count()
            #
            # msg = Message(MessageType.PARSER_SUMMARY, (line_number, err_cnt))
            # self.send_message(msg)

        except FileNotFoundError:
            self.error_handler.abort_translation('IO_ERROR', self)

    def get_error_count(self):
        return self.error_handler.get_error_count()

    def get_iCode(self):
        return self.iCode

    def get_symTab(self):
        return self.symtab_stack

    def get_line(self):
        return self.scanner.source.line

    def synchronize(self, syncset, ptt_set=[]):
        token = self.current_token()

        if token.type == TokenType.EOF:
            return token
        if token.ptype in ptt_set:
            sync = True
        elif (token.ptype == PTT.IDENTIFIER) and ('IDENTIFIER' in syncset):
            sync = True
        elif token.value in syncset:
            sync = True
        else:
            sync = False

        if not sync:
            self.error_handler.flag(token, 'UNEXPECTED_TOKEN', self)

            token = self.next_token()
            while (token.type != TokenType.EOF) and (not token.value in syncset):
                token = self.next_token()

        return token


class BlockParser(PascalParserTD):
    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token, routine_id):
        declaration_parser = DeclarationsParser(self)
        statement_parser = StatementParser(self)

        declaration_parser.parse(token, routine_id)

        token = self.synchronize(StatementParser.STMT_START_SET)
        root_node = None
        if token.type == TokenType.EOF:
            self.error_handler.flag(token, 'UNEXPECTED EOF', self)
            return None

        if token.ptype == PTT.RESERVED and  token.value == 'BEGIN':
            root_node = statement_parser.parse(token)
        else:
            self.error_handler.flag(token, 'MISSING_BEGIN', self)
            if token.value in StatementParser.STMT_START_SET:
                root_node = iCodeNodeFactory().create('COMPOUND')
                statement_parser.parse_list(token, root_node, 'END', 'MISSING_END')

        return root_node


class DeclarationsParser(PascalParserTD):
    DECLARATION_START_SET = ['CONST', 'TYPE', 'VAR', 'PROCEDURE', 'FUNCTION', 'BEGIN']
    TYPE_START_SET = copy.deepcopy(DECLARATION_START_SET)
    TYPE_START_SET.remove('CONST')
    VAR_START_SET = copy.deepcopy(TYPE_START_SET)
    VAR_START_SET.remove('TYPE')
    ROUTINE_START_SET = copy.deepcopy(VAR_START_SET)
    ROUTINE_START_SET.remove('VAR')

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token, parent_id):
        from pascal.pascal_parser_routine import DeclaredRoutineParser

        token = self.synchronize(DeclarationsParser.DECLARATION_START_SET)
        if token.ptype == PTT.RESERVED and token.value == 'CONST':
            token = self.next_token()
            constant_definition_parser = ConstantDefinitionsParser(self)
            constant_definition_parser.parse(token, None)

        token = self.synchronize(self.TYPE_START_SET)
        if token.ptype == PTT.RESERVED and token.value == 'TYPE':
            token = self.next_token()
            type_defination_parser = TypeDefinitionsParser(self)
            type_defination_parser.parse(token, None)

        token = self.synchronize(self.VAR_START_SET)
        if token.type == TokenType.EOF:
            self.error_handler.flag(token, 'UNEXPECTED_EOF', self)
            return

        if token.ptype == PTT.RESERVED and token.value == 'VAR':
            token = self.next_token()
            variable_declarations_parser = VariableDeclarationsParser(self)
            variable_declarations_parser.set_definition(Definition.VARIABLE)
            variable_declarations_parser.parse(token, None)

        token = self.synchronize(DeclarationsParser.ROUTINE_START_SET)

        while token.value == 'PROCEDURE' or token.value == 'FUNCTION':
            routine_parser = DeclaredRoutineParser(self)
            routine_parser.parse(token, parent_id)

            token = self.current_token()
            if token.value == 'SEMICOLON':
                while token.value == 'SEMICOLON':
                    token = self.next_token()

            token = self.synchronize(self.ROUTINE_START_SET)

        return None

class StatementParser(PascalParserTD):
    STMT_START_SET = ['BEGIN', 'CASE', 'FOR', 'IF', 'REPEAT', 'WHILE', 'IDENTIFIER', 'SEMICOLON']
    STMT_FOLLOW_SET = ['SEMICOLON', 'END', 'ELSE', 'UNTIL', 'DOT']

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        if token.ptype == PTT.RESERVED and  token.value == 'BEGIN':
            statement_node = CompoundStatementParser(self).parse(token)
        elif token.ptype == PTT.IDENTIFIER:
            # statement_node = AssignmentStatementParser(self).parse(token)
            name = token.value.lower()
            id = Parser.symtab_stack.lookup(name)
            if id:
                id_defn = id.get_definition()
            else:
                id_defn = Predefined.undefined_type

            if id_defn == Definition.VARIABLE or id_defn == Definition.VALUE_PARM or id_defn == Definition.VAR_PARM \
                    or id_defn == Definition.UNDEFINED:
                assignment_parser = AssignmentStatementParser(self)
                statement_node = assignment_parser.parse(token)
            elif id_defn == Definition.FUNCTION:
                assignment_parser = AssignmentStatementParser(self)
                statement_node = assignment_parser.parse(token)
            elif id_defn == Definition.PROCEDURE:
                call_parser = CallParser(self)
                statement_node = call_parser.parse(token)
            else:
                self.error_handler.flag(token, 'UNEXPECTED_TOKEN', self)
                token = self.next_token()
        elif token.ptype == PTT.RESERVED and  token.value == 'REPEAT':
            statement_node = RepeatStatementParser(self).parse(token)
        elif token.ptype == PTT.RESERVED and  token.value == 'WHILE':
            statement_node = WhileStatementParser(self).parse(token)
        elif token.ptype == PTT.RESERVED and  token.value == 'FOR':
            statement_node = ForStatementParser(self).parse(token)
        elif token.ptype == PTT.RESERVED and  token.value == 'IF':
            statement_node = IfStatementParser(self).parse(token)
        elif token.ptype == PTT.RESERVED and  token.value == 'CASE':
            statement_node = CaseStatementParser(self).parse(token)
        else:
            statement_node = iCodeNodeFactory().create('NO_OP')
        set_line_number(statement_node, token)
        return statement_node

    def parse_list(self, token, parent_node, terminator, err_code):
        terminator_set = StatementParser.STMT_START_SET + [terminator]

        while token.type != TokenType.EOF and token.value != terminator:
            statement_node = self.parse(token)
            parent_node.add_child(statement_node)

            token = self.current_token()

            if token.value == 'SEMICOLON':
                token = self.next_token()
            elif token.ptype == PTT.IDENTIFIER:
                self.error_handler.flag(token, 'MISSING_SEMICOLLON', self)

            token = self.synchronize(terminator_set)
            if token == None:
                self.error_handler.flag(token, err_code, self)
                return

        if token.value == terminator:
            token = self.next_token()
        else:
            self.error_handler.flag(token, err_code, self)



class VariableParser(StatementParser):
    SUBSCRIPT_FIELD_START_SET = ['LEFT_BRACKET', 'DOT']
    RIGHT_BRACKET_SET = ['RIGHT_BRACKET', 'EQUALS', 'SEMICOLON']

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        name = token.value.lower()
        variable_id = Parser.symtab_stack.lookup(name)

        if not variable_id:
            self.error_handler.flag(token, 'IDENTIFIER_UNDEFINED', self)
            variable_id = Parser.symtab_stack.enter_local(name)
            variable_id.set_definition('UNDEFINED')
            variable_id.set_typespec(Predefined.undefined_type)

        return self.parse_variable_id(token, variable_id)

    def parse_variable_id(self, token, variable_id):
        defn_code = variable_id.get_definition()
        if defn_code != Definition.VARIABLE and defn_code != Definition.VALUE_PARM and defn_code != Definition.VAR_PARM:
            self.error_handler.flag(token, 'INVALID_IDENTIFIER_USAGE', self)

        variable_node = iCodeNodeFactory().create('VARIABLE')
        variable_node.set_attribute('ID', variable_id)
        token = self.next_token()

        variable_type = variable_id.get_typespec()

        while token.value in self.SUBSCRIPT_FIELD_START_SET:
            if token.ptype == PascalSpecialSymbol.LEFT_BRACKET:
                sub_fld_node = self.parse_subscripts(variable_type)
            else:
                sub_fld_node = self.parse_field(variable_type)

            token = self.current_token()
            variable_type = sub_fld_node.get_typespec()
            variable_node.add_child(sub_fld_node)

        variable_node.set_typespec(variable_type)
        return variable_node

    def parse_subscripts(self, variable_type):
        expression_parer = ExpressionParser(self)
        subscript_node = iCodeNodeFactory().create('SUBSCRIPTS')

        first = True
        while first or token.ptype == PascalSpecialSymbol.COMMA:
            first = False
            token = self.next_token()
            if variable_type.get_form() == TypeForm.ARRAY:
                expr_node = expression_parer.parse(token)
                if expr_node:
                    expr_type = expr_node.get_typespec()
                else:
                    expr_type = Predefined.undefined_type

                index_type = variable_type.get_attribute('ARRAY_INDEX_TYPE')
                if not TypeChecker().are_assignment_compatible(index_type, expr_type):

                    self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

                subscript_node.add_child(expr_node)

                variable_type = variable_type.get_attribute('ARRAY_ELEMENT_TYPE')
            else:
                self.error_handler.flag(token, 'TOO_MANY_SUBSCRIPTS', self)
                expression_parer.parse(token)

            token = self.current_token()

        token = self.synchronize(self.RIGHT_BRACKET_SET)
        if token.ptype == PascalSpecialSymbol.RIGHT_BRACKET:
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_RIGHT_BRACKET', self)

        subscript_node.set_typespec(variable_type)
        return subscript_node

    def parse_field(self, variable_type):
        field_node = iCodeNodeFactory().create('FIELD')

        token = self.next_token()
        variable_form = variable_type.get_form()

        if token.ptype == PTT.IDENTIFIER and variable_form == TypeForm.RECORD:
            symtab = variable_type.get_attribute('RECORD_SYMTAB')
            field_name = token.value.lower()
            filedid = symtab.lookup(field_name)

            if filedid:
                variable_type = filedid.get_typespec()
                filedid.append_line_number(token.line_num)
                field_node.set_attribute('ID', filedid)
            else:
                self.error_handler.flag(token, 'INVALID_FIELD', self)
        else:
            self.error_handler.flag(token, 'INVALID_FIELD', self)

        token = self.next_token()
        field_node.set_typespec(variable_type)
        return field_node

class CompoundStatementParser(StatementParser):
    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        token = self.next_token()
        compound_node = iCodeNodeFactory().create('COMPOUND')
        statement_parser = StatementParser(self)
        statement_parser.parse_list(token, compound_node, 'END', 'MISSING_END')
        return compound_node


class ExpressionParser(StatementParser):
    EXPR_START_SET = ['PLUS', 'MINUS', 'NOT', 'LEFT_PAREN']
    EXPR_START_SET_PTT = [PTT.IDENTIFIER, PTT.INTEGER, PTT.REAL, PTT.STRING]

    def __init__(self, parent):
        super().__init__(parent)
        self.op_map =  {'EQUALS' : 'EQ',
                        'NOT_EQUALS' : 'NE',
                        'LESS_THAN':  'LT',
                        'LESS_EQUALS' : 'LE',
                        'GREATER_THAN' : 'GT',
                        'GREATER_EQUALS' : 'GE',
                        'PLUS' : 'ADD',
                        'MINUS' : 'SUBTRACT',
                        'OR' : 'OR',
                        'STAR' : 'MULTIPLY',
                        'SLASH' : 'FLOAT_DIVIDE',
                        'DIV' : 'INTEGER_DIVIDE',
                        'MOD' : 'MOD',
                        'AND' : 'AND'
        }
        self.add_ops = ['PLUS', 'MINUS', 'OR']
        self.mul_ops = ['STAR', 'SLASH', 'DIV', 'MOD', 'AND']

    def parse(self, token):
        return self.parse_expression(token)

    def parse_expression(self, token):
        root_node = self.parse_simple_expression(token)
        if root_node:
            result_type = root_node.get_typespec()
        else:
            result_type = Predefined.undefined_type

        token = self.current_token()
        token_type = token.value

        if token_type in self.op_map:
            node_type = self.op_map[token_type]
            opnode = iCodeNodeFactory().create(node_type)
            opnode.add_child(root_node)

            token = self.next_token()
            sim_expr_node = self.parse_simple_expression(token)
            opnode.add_child(sim_expr_node)
            root_node = opnode

            if sim_expr_node:
                sim_expr_type = sim_expr_node.get_typespec()
            else:
                sim_expr_type = Predefined.undefined_type

            if TypeChecker().are_comparison_compatible(result_type, sim_expr_type):
                result_type = Predefined.boolean_type
            else:
                self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

            if root_node:
                root_node.set_typespec(result_type)

        return root_node

    def parse_simple_expression(self, token):
        sign_token = None
        sign_type = None

        token_type = token.value
        if token_type == 'PLUS' or token_type == 'MINUS':
            sign_type = token_type
            sign_token = copy.copy(token)
            token = self.next_token()

        root_node = self.parse_term(token)
        if root_node:
            result_type = root_node.get_typespec()
        else:
            result_type = Predefined.undefined_type

        if sign_type and (not TypeChecker.is_integer_or_real(result_type)):
            self.error_handler.flag(sign_token, 'INCOMPATIBLE_TYPES', self)

        if sign_type == 'MINUS':
            negate_node = iCodeNodeFactory().create('NEGATE')
            negate_node.add_child(root_node)
            negate_node.set_typespec(root_node.get_typespec())
            root_node = negate_node

        token = self.current_token()
        token_type = token.value

        while token_type in self.add_ops:
            operator = token_type
            node_type = self.op_map[operator]
            op_node = iCodeNodeFactory().create(node_type)
            op_node.add_child(root_node)

            token = self.next_token()
            term_node = self.parse_term(token)
            op_node.add_child(term_node)

            if term_node:
                term_type = term_node.get_typespec()
            else:
                term_type = Predefined.undefined_type

            root_node = op_node

            if operator == 'PLUS' or operator == 'MINUS':
                if TypeChecker().are_both_integer(result_type, term_type):
                    result_type = Predefined.integer_type
                elif TypeChecker().is_at_least_one_real(result_type, term_type):
                    result_type = Predefined.real_type
                else:
                    self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)
            elif operator == 'OP':
                if TypeChecker().are_both_boolean(result_type, term_type):
                    result_type = Predefined.boolean_type
                else:
                    self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

            root_node.set_typespec(result_type)

            token = self.current_token()
            token_type = token.value

        return root_node

    def parse_term(self, token):
        root_node = self.parse_factor(token)
        if root_node:
            result_type = root_node.get_typespec()
        else:
            result_type = Predefined.undefined_type

        token = self.current_token()
        token_type = token.value

        while token_type in self.mul_ops:
            operator = token_type
            node_type = self.op_map[operator]
            op_node = iCodeNodeFactory().create(node_type)
            op_node.add_child(root_node)

            token = self.next_token()
            factor_node = self.parse_factor(token)
            op_node.add_child(factor_node)
            if factor_node:
                factor_type = factor_node.get_typespec()
            else:
                factor_type = Predefined.undefined_type

            root_node = op_node

            if operator == 'START':
                if TypeChecker().are_both_integer(result_type, factor_type):
                    result_type = Predefined.undefined_type
                elif TypeChecker().is_at_least_one_real(result_type, factor_type):
                    result_type = Predefined.real_type
                else:
                    self.error_handler.flag(self, 'INCOMPATIBLE_TYPES', self)
            elif operator == 'SLASH':
                if TypeChecker().are_both_integer(result_type, factor_type):
                    result_type = Predefined.real_type
                else:
                    self.error_handler.flag(self, 'INCOMPATIBLE_TYPES', self)
            elif operator == 'DIV' or operator == 'MOD':
                if TypeChecker().are_both_integer(result_type, factor_type):
                    result_type = Predefined.real_type
                else:
                    self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)
            elif operator == 'AND':
                if TypeChecker().are_both_boolean(result_type, factor_type):
                    result_type = Predefined.boolean_type
                else:
                    self.error_handler(token,  'INCOMPATIBLE_TYPES', self)

            root_node.set_typespec(result_type)
            token = self.current_token()
            token_type = token.value

        return root_node

    def parse_factor(self, token):
        ptype = token.ptype
        root_node = None
        if ptype == PTT.IDENTIFIER:
            return self.parse_identifier(token)
        elif ptype == PTT.INTEGER:
            root_node = iCodeNodeFactory().create('INTEGER_CONSTANT')
            root_node.set_attribute('VALUE', token.value)
            root_node.set_typespec(Predefined.integer_type)
            token = self.next_token()

        elif ptype == PTT.REAL:
            root_node = iCodeNodeFactory().create('REAL_CONSTANT')
            root_node.set_attribute('VALUE', token.value)
            root_node.set_typespec(Predefined.real_type)
            token = self.next_token()

        elif ptype == PTT.STRING:
            root_node = iCodeNodeFactory().create('STRING_CONSTANT')
            root_node.set_attribute('VALUE', token.value)
            if len(token.value) == 1:
                result_type = Predefined.char_type
            else:
                result_type = TypeSpec(value)
            root_node.set_typespec(result_type)
            token = self.next_token()

        elif token.value == 'NOT':
            token = self.next_token()
            root_node = iCodeNodeFactory().create('NOT')
            factor_node = self.parser_factor(token)
            root_node.set_attributes(factor_node)
            if factor_node:
                factor_type = factor_node.get_typespec()
            else:
                factor_type = Predefined.undefined_type

            if not TypeChecker().is_bool(factor_type):
                self.error_handler(token, 'INCOMPATIBLE_TYPES', self)
            root_node.set_typespec(Predefined.boolean_type)

        elif token.value == 'LEFT_PAREN':
            token = self.next_token()
            root_node = self.parse_expression(token)
            if root_node:
                result_type = root_node.get_typespec()
            else:
                result_type = Predefined.undefined_type

            token = self.current_token()
            if token.value == 'RIGHT_PAREN':
                token = self.next_token()
            else:
                self.error_handler.flag(token, 'MISSING_RIGHT_PAREN', self)
            root_node.set_typespec(result_type)

        else:
            self.error_handler.flag(token, 'UNEXPECTED_TOKEN', self)

        return root_node

    def parse_identifier(self, token):
        root_node = None
        name = token.value.lower()
        id = Parser.symtab_stack.lookup(name)

        if not id:
            self.error_handler.flag(token, 'IDENTIFIER_UNDEFINED', self)
            id = Parser.symtab_stack.enter_local(name)
            id.set_definition(Definition.UNDEFINED)
            id.set_typespec(Predefined.undefined_type)

        defn_code = id.get_definition()

        if defn_code == Definition.CONSTANT:
            value = id.get_attribute('CONSTANT_VALUE')
            type = id.get_typespec()

            if isinstance(value, int):
                root_node = iCodeNodeFactory().create('INTEGER_CONSTANT')
                root_node.set_attribute('VALUE', value)
            elif isinstance(value, float):
                root_node = iCodeNodeFactory().create('REAL_CONSTANT')
                root_node.set_attribute('VALUE', value)
            elif isinstance(value, str):
                root_node = iCodeNodeFactory().create('STRING_CONSTANT')
                root_node.set_attribute('VALUE', value)

            id.append_line_number(token.line_num)
            token = self.next_token()

            if root_node:
                root_node.set_typespec(type)

        elif defn_code == Definition.ENUMERATION_CONSTANT:
            value = id.get_attribute('CONSTANT_VALUE')
            type = id.get_typespec()

            root_node = iCodeNodeFactory().create('INTEGER_CONSTANT')
            root_node.set_attribute('VALUE', value)

            id.append_line_number(token.line_num)
            token = self.next_token()
            root_node.set_typespec(type)
        elif defn_code == Definition.FUNCTION:
            call_parser = CallParser(self)
            root_node = call_parser.parse(token)
        else:
            variable_parser = VariableParser(self)
            root_node = variable_parser.parse(token)

        return root_node


class AssignmentStatementParser(StatementParser):
    COLON_EQUALS_SET = copy.deepcopy(ExpressionParser.EXPR_START_SET) + ['COLON_EQUALS'] + \
                       copy.deepcopy(StatementParser.STMT_FOLLOW_SET)

    def __init__(self, parent):
        self.is_function_target = False
        super().__init__(parent)

    def parse(self, token):
        assigin_node = iCodeNodeFactory().create('ASSIGN')
        variable_parser = VariableParser(self)

        if self.is_function_target:
            target_node = variable_parser.parse_function_name_target(token)
        else:
            target_node = variable_parser.parse(token)

        if target_node:
            target_type = target_node.get_typespec()
        else:
            target_type = Predefined.undefined_type

        assigin_node.add_child(target_node)
        token = self.synchronize(self.COLON_EQUALS_SET)
        if token.value == 'COLON_EQUALS':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_COLON_EQUALS', self)

        expression_parser = ExpressionParser(self)
        expr_node = expression_parser.parse(token)
        assigin_node.add_child(expr_node)

        if expr_node:
            expr_type = expr_node.get_typespec()
        else:
            expr_type = Predefined.undefined_type

        if not TypeChecker().are_assignment_compatible(target_type, expr_type):
            self.error_handler.flag(token , 'INCOMPATIBLE_TYPES', self)

        assigin_node.set_typespec(target_type)
        return assigin_node

    def parse_function_name_assignment(self, token):
        self.is_function_target = True
        return self.parse(token)


class CaseStatementParser(StatementParser):
    def __init__(self, parent):
        super().__init__(parent)
        self.CONSTANT_START_SET = [ 'PLUS', 'MINUS']
        self.CONSTANT_START_SET_PTT = [PTT.IDENTIFIER, PTT.INTEGER, PTT.STRING]
        self.OF_SET = self.CONSTANT_START_SET + ['OF'] + StatementParser.STMT_FOLLOW_SET
        self.COMMA_SET = self.CONSTANT_START_SET + ['COMMA', 'COLON'] +StatementParser.STMT_START_SET + StatementParser.STMT_FOLLOW_SET

    # CaseStatementParser
    def parse(self, token):
        token = self.next_token()
        select_node = iCodeNodeFactory().create('SELECT')

        expression_parser = ExpressionParser(self)
        expr_node = expression_parser.parse(token)
        select_node.add_child(expr_node)
        if expr_node:
            expr_type = expr_node.get_typespec()
        else:
            expr_type = Predefined.undefined_type

        if (not TypeChecker().is_integer(expr_type)) and (not TypeChecker().is_char(expr_type)) and expr_type.get_form() != TypeForm.ENUMERATION:
            self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

        token = self.synchronize(self.OF_SET)
        if token.value == 'OF':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_OF', self)

        constain_set = []
        while token.type != TokenType.EOF and token.value != 'END':
            select_node.add_child(self. parse_branch(token, expr_type, constain_set))
            token = self.current_token()
            token_type = token.value
            if token_type == 'SEMICOLON':
                token = self.next_token()
            elif token_type in self.CONSTANT_START_SET:
                self.error_handler.flag(token, 'MISSING_SEMICOLON', this)

        if token.value == 'END':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_END', self)

        return select_node

    def parse_branch(self, token, expr_type, constant_set):
        branch_node = iCodeNodeFactory().create('SELECT_BRANCH')
        constants_node = iCodeNodeFactory().create('SELECT_CONSTANTS')
        branch_node.add_child(constants_node)

        self.parse_constant_list(token, expr_type, constants_node, constant_set)
        token = self.current_token()

        if token.value == 'COLON':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_COLON', self)

        statement_parser = StatementParser(self)
        branch_node.add_child(statement_parser.parse(token))

        return branch_node

    def parse_constant_list(self, token, expr_type, constants_node, constants_set):
        while token.value in self.CONSTANT_START_SET or token.ptype in self.CONSTANT_START_SET_PTT:
            constants_node.add_child(self.parse_constant(token, expr_type, constants_set))
            token = self.synchronize(self.COMMA_SET)

            if token.value == 'COMMA':
                token = self.next_token()
            elif token.value in self.CONSTANT_START_SET:
                self.error_handler.flag(token, 'MISSING_COMMA', self)

    def parse_constant(self, token, expr_type, constants_set):
        sign = None
        constant_node = None
        constant_type = None

        token = self.synchronize(self.CONSTANT_START_SET, ptt_set = self.CONSTANT_START_SET_PTT)
        token_type = token.value

        if token_type == 'PLUS' or token_type == 'MINUS':
            sign = token_type
            token = self.next_token()

        if token.ptype == PTT.IDENTIFIER:
            constant_node = self.parse_identifier_constant(token, sign)
            if constant_node:
                constant_type = constant_node.get_typespec()
        elif token.ptype == PTT.INTEGER:
            constant_node = self.parse_integer_constant(token.value, sign)
            constant_type = Predefined.integer_type
        elif token.ptype == PTT.STRING:
            constant_node = self.parse_character_constant(token, token.value, sign)
            constant_type = Predefined.char_type
        else:
            self.error_handler.flag(token, 'INVALID_CONSTANT', self)

        if constant_node != None:
            value = constant_node.get_attribute('VALUE')
            if value in constants_set:
                self.error_handler.flag(token, 'CASE_CONSTANT_REUSED', self)
            else:
                constants_set.append(value)

        if not TypeChecker().are_comparison_compatible(expr_type, constant_type):
            self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)
            token = self.next_token()
            return None

        token = self.next_token()
        constant_node.set_typespec(constant_type)
        return constant_node

    def parse_identifier_constant(self, token, sign):
        const_node = None
        const_type = None

        name = token.value.lower()
        id = Parser.symtab_stack.lookup(name)

        if not id:
            id = Parser.symtab_stack.enter_local(name)
            id.set_definition(Definition.UNDEFINED)
            id.set_typespec(Predefined.undefined_type)
            self.error_handler.flag(token, 'IDENTIFIER_UNDEFINED', self)
            return None

        defn_code = id.get_definition()
        if defn_code == Definition.CONSTANT or defn_code == Definition.ENUMERATION_CONSTANT:
            const_value = id.get_attribute('CONSTANT_VALUE')
            const_type = id.get_typespec()

            if sign and (not TypeChecker().is_integer(const_type)):
                self.error_handler.flag(token, 'INVALID_CONSTANT', self)

            const_node = iCodeNodeFactory().create('INTEGER_CONSTANT')
            const_node.set_attribute('VALUE', const_value)

        id.append_line_number(token.line_num)
        if const_node:
            const_node.set_typespec(const_type)

        return const_node

    def parse_integer_constant(self, value, sign):
        constant_node = iCodeNodeFactory().create('INTEGER_CONSTANT')
        int_value = int(value)
        if sign == 'MINUS':
            int_value = -int_value

        constant_node.set_attribute('VALUE', int_value)
        return constant_node

    def parse_character_constant(self, token, value, sign):
        constant_node = None

        if sign != None:
            self.error_handler.flag(token, 'INVALID_CONSTANT', self)
        else:
            if len(value) == 1:
                constant_node = iCodeNodeFactory().create('STRING_CONSTANT')
                constant_node.set_attribute('VALUE', value)
            else:
                self.error_handler.flag(token, 'STRING_CONSTANT', self)

        return constant_node


class ForStatementParser(StatementParser):
    TO_DOWNTO_SET = ExpressionParser.EXPR_START_SET + ['TO', 'DOWNTO'] + StatementParser.STMT_FOLLOW_SET
    TO_DOWNTO_SET_PTT = ExpressionParser.EXPR_START_SET_PTT
    DO_SET = StatementParser.STMT_START_SET + ['DO'] + StatementParser.STMT_FOLLOW_SET

    def __init__(self, parent):
        super().__init__(parent)

    # ForStatementParser
    def parse(self, token):
        token = self.next_token()
        target_token = token

        compound_node = iCodeNodeFactory().create('COMPOUND')
        loop_node = iCodeNodeFactory().create('LOOP')
        test_node = iCodeNodeFactory().create('TEST')

        assignment_parser = AssignmentStatementParser(self)
        init_assign_node = assignment_parser.parse(token)
        if init_assign_node:
            control_type = init_assign_node.get_typespec()
        else:
            control_type = Predefined.undefined_type

        set_line_number(init_assign_node, token)

        if (not TypeChecker().is_integer(control_type)) and (not control_type.get_from == TypeForm.ENUMERATION):
            self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

        compound_node.add_child(init_assign_node)
        compound_node.add_child(loop_node)

        token = self.synchronize(ForStatementParser.TO_DOWNTO_SET, ptt_set=ForStatementParser.TO_DOWNTO_SET_PTT)
        direction = token.value

        if direction == 'TO' or direction == 'DOWNTO':
            token = self.next_token()
        else:
            direction = 'TO'
            self.error_handler.flag(token, 'MISSING_TO_DOWNTO', self)

        if direction == 'TO':
            rel_op_node = iCodeNodeFactory().create('GT')
        else:
            rel_op_node = iCodeNodeFactory().create('LT')

        rel_op_node.set_typespec(Predefined.boolean_type)
        control_var_node = init_assign_node.get_children()[0]
        rel_op_node.add_child(control_var_node)

        expression_parser = ExpressionParser(self)
        expr_node = expression_parser.parse(token)
        rel_op_node.add_child(expr_node)

        if expr_node:
            expr_type = expr_node.get_typespec()
        else:
            expr_type = Predefined.undefined_type

        if not TypeChecker().are_assignment_compatible(control_type, expr_type):
            self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

        test_node.add_child(rel_op_node)
        loop_node.add_child(test_node)

        token = self.synchronize(ForStatementParser.DO_SET)
        if token.value == 'DO':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_DO', self)

        statement_parser = StatementParser(self)
        loop_node.add_child(statement_parser.parse(token))

        next_assign_node = iCodeNodeFactory().create('ASSIGN')
        next_assign_node.set_typespec(control_type)
        next_assign_node.add_child(copy.copy(control_var_node))

        if direction == 'TO':
            arith_op_node = iCodeNodeFactory().create('ADD')
        else:
            arith_op_node = iCodeNodeFactory().create('SUBTRACT')

        arith_op_node.get_typespec(Predefined.integer_type)
        arith_op_node.add_child(control_var_node)
        one_node = iCodeNodeFactory().create('INTEGER_CONSTANT')
        one_node.set_attribute('VALUE', 1)
        one_node.set_typespec(Predefined.integer_type)
        arith_op_node.add_child(one_node)

        next_assign_node.add_child(arith_op_node)
        loop_node.add_child(next_assign_node)

        set_line_number(next_assign_node, target_token)

        return compound_node


class IfStatementParser(StatementParser):
    THEN_SET = StatementParser.STMT_START_SET + ['THEN'] + StatementParser.STMT_FOLLOW_SET

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        token = self.next_token()

        if_node = iCodeNodeFactory().create('IF')
        expression_parser = ExpressionParser(self)
        expr_node = expression_parser.parse(token)
        if_node.add_child(expr_node)

        if expr_node:
            expr_type = expr_node.get_typespec()
        else:
            expr_type = Predefined.undefined_type

        if not TypeChecker().is_bool(expr_type):
            self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

        token = self.synchronize(IfStatementParser.THEN_SET)
        if token.value == 'THEN':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_THEN', self)

        statement_parser = StatementParser(self)
        if_node.add_child(statement_parser.parse(token))
        token = self.current_token()

        if token.value == 'ELSE':
            token = self.next_token()
            else_node = statement_parser.parse(token)
            if_node.add_child(else_node)

        return if_node


class RepeatStatementParser(StatementParser):
    THEN_SET = StatementParser.STMT_START_SET + ['THEN'] + StatementParser.STMT_FOLLOW_SET

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        token = self.next_token()
        loop_node = iCodeNodeFactory().create('LOOP')
        test_node = iCodeNodeFactory().create('TEST')

        statement_parser = StatementParser(self)
        statement_parser.parse_list(token, loop_node, 'UNTIL', 'MISSING_UNTIL')
        token = self.current_token()

        express_parser = ExpressionParser(self)
        expr_node = express_parser.parse(token)
        test_node.add_child(expr_node)
        loop_node.add_child(test_node)

        if expr_node:
            expr_type = expr_node.get_typespec()
        else:
            expr_type = Predefined.undefined_type

        if not TypeChecker().is_bool(expr_type):
            self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

        return loop_node


class WhileStatementParser(StatementParser):
    DO_SET = StatementParser.STMT_START_SET + ['DO'] + StatementParser.STMT_FOLLOW_SET

    def __init__(self, parent):
        super().__init__(parent)

    # CaseStatementParser
    def parse(self, token):
        token = self.next_token()

        loop_node = iCodeNodeFactory().create('LOOP')
        break_node = iCodeNodeFactory().create('TEST')
        not_node = iCodeNodeFactory().create('NOT')

        loop_node.add_child(break_node)
        break_node.add_child(not_node)

        expression_parser = ExpressionParser(self)
        expr_node = expression_parser.parse(token)
        not_node.add_child(expr_node)

        if expr_node:
            expr_type = expr_node.get_typespec()
        else:
            expr_type = Predefined.undefined_type

        if not TypeChecker().is_bool(expr_type):
            self.error_handler.flag(token, 'INCOMPATIBLE_TYPES', self)

        token = self.synchronize(WhileStatementParser.DO_SET)
        if token.value == 'DO':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_DO', self)

        statement_parser = StatementParser(self)
        loop_node.add_child(statement_parser.parse(token))

        return loop_node


class ConstantDefinitionsParser(DeclarationsParser):
    IDENTIFIER_SET = copy.deepcopy(DeclarationsParser.TYPE_START_SET)
    IDENTIFIER_SET.append('IDENTIFIER')
    CONSTANT_START_SET = ['PLUS', 'MINUS', 'SEMICOLON']
    CONSTANT_START_SET_PTT = [PTT.IDENTIFIER, PTT.INTEGER, PTT.REAL, PTT.STRING]
    EQUALS_SET = copy.deepcopy(CONSTANT_START_SET)
    EQUALS_SET.append('EQUALS')
    EQUALS_SET.append('SEMICOLON')
    NEXT_START_SET = copy.deepcopy(DeclarationsParser.TYPE_START_SET)
    NEXT_START_SET.append('SEMICOLON')
    NEXT_START_SET.append('IDENTIFIER')

    def __init__(self, parent):
        super().__init__(parent)

    # ConstantDefinitionsParser
    def parse(self, token, parent_id):
        token = self.synchronize(ConstantDefinitionsParser.IDENTIFIER_SET)
        while token.ptype == PTT.IDENTIFIER:
            name = token.value.lower()
            constant_id = Parser.symtab_stack.lookup_local(name)

            if not constant_id:
                constant_id = Parser.symtab_stack.enter_local(name)
                constant_id.append_line_number(token.line_num)
            else:
                self.error_handler.flag(token, 'IDENTIFIER_REDEFINED', self)
                constant_id = None

            token = self.next_token()
            token = self.synchronize(ConstantDefinitionsParser.EQUALS_SET)

            if token.value == 'EQUALS':
                token = self.next_token()
            else:
                self.error_handler.flag(token, 'MISSING_EQUALS', self)

            constant_token = copy.copy(token)
            value = self.parse_constant(token)

            if constant_id:
                constant_id.set_definition(Definition.CONSTANT)
                constant_id.set_attribute('CONSTANT_VALUE', value)

                if constant_token.ptype == PTT.IDENTIFIER:
                    constant_type = self.get_constant_type_token(constant_token)
                else:
                    constant_type = self.get_constant_type_value(value)
                constant_id.set_typespec(constant_type)

            token = self.current_token()
            if token.value == 'SEMICOLON':
                while token.value == 'SEMICOLON':
                    token = self.next_token()
            elif token.value in ConstantDefinitionsParser.NEXT_START_SET:
                self.error_handler.flag(token, 'MISSING_SEMICOLON', self)

            token = self.synchronize(ConstantDefinitionsParser.IDENTIFIER_SET)

        return None

    def parse_constant(self, token):
        sign = None

        token = self.synchronize(ConstantDefinitionsParser.CONSTANT_START_SET, ptt_set=self.CONSTANT_START_SET_PTT)
        if token.value == 'PLUS' or token.value == 'MINUS':
            sign = token.value
            token = self.next_token()

        if token.ptype == PTT.IDENTIFIER:
            return self.parse_identifier_constant(token, sign)
        elif token.ptype == PTT.INTEGER:
            value = int(token.value)
            token = self.next_token()
            if sign == 'MINUS':
                return -value
            else:
                return value
        elif token.ptype == PTT.REAL:
            value = float(token.value)
            self.next_token()
            if sign == 'MINUS':
                return -value
            else:
                return value
        elif token.ptype == PTT.STRING:
            if sign:
                self.error_handler.flag(token, 'INVALID_CONSTANT', self)
            self.next_token()
            return str(token.value)
        else:
            self.error_handler.flag(token, 'INVALID_CONSTANT', self)
            return None

    def parse_identifier_constant(self, token, sign):
        name = token.value.lower()
        id = Parser.symtab_stack.lookup(name)

        self.next_token()

        if not id:
            self.error_handler.flag(token, 'IDENTIFIER_UNDEFINED', self)
            return None

        definition = id.get_definition()

        if definition == Definition.CONSTANT:
            value = id.get_attribute('CONSTANT_VALUE')
            id.append_line_number(token.line_num)

            if isinstance(value, int):
                if sign == 'MINUS':
                    return -int(value)
                else:
                    return value
            elif isinstance(value, float):
                if sign == 'MINUS':
                    return -float(value)
                else:
                    return value
            elif isinstance(value, str):
                if sign:
                    self.error_handler.flag(token, 'INVALID_CONSTANT', self)
                return value
            else:
                return None
        elif definition == Definition.ENUMERATION_CONSTANT:
            value = id.get_attribute('CONSTANT_VALUE')
            id.append_line_number(token.line_num)
            if sign:
                self.error_handler.flag(token, 'INVALID_CONSTANT', self)
            return value
        elif not definition:
            self.error_handler.flag(token, 'NOT_CONSTANT_IDENTIFIER', self)
            return None
        else:
            self.error_handler.flag(token, 'INVALID_CONSTANT', self)
            return None

    def get_constant_type_value(self, value):
        if isinstance(value, int):
            return Predefined.integer_type
        elif isinstance(value, float):
            return Predefined.real_type
        elif isinstance(value, str):
            if len(value) == 1:
                return Predefined.char_type
            else:
                return TypeSpec(value)
        return None

    def get_constant_type_token(self, identifier):
        name = identifier.value.lower()
        id = Parser.symtab_stack.lookup(name)

        if not id:
            return None
        definition = id.get_definition()
        if definition == Definition.CONSTANT or definition == Definition.ENUMERATION_CONSTANT:
            return id.get_typespec()
        return None


class TypeDefinitionsParser(DeclarationsParser):
    IDENTIFIER_SET = copy.deepcopy(DeclarationsParser.VAR_START_SET)
    IDENTIFIER_SET_PTT = [PTT.IDENTIFIER]
    EQUALS_SET = copy.deepcopy(ConstantDefinitionsParser.CONSTANT_START_SET)
    EQUALS_SET.append('EQUALS')
    EQUALS_SET.append('SEMICOLON')
    FOLLOW_SET = ['SEMICOLON']
    NEXT_START_SET = copy.deepcopy(DeclarationsParser.VAR_START_SET)
    NEXT_START_SET.append('SEMICOLON')
    NEXT_START_SET.append('IDENTIFIER')

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token, parent_id):
        token = self.synchronize(self.IDENTIFIER_SET, ptt_set=self.IDENTIFIER_SET_PTT)

        while token.ptype == PTT.IDENTIFIER:
            name = token.value.lower()
            type_id = Parser.symtab_stack.lookup(name)

            if not type_id:
                type_id = Parser.symtab_stack.enter_local(name)
                type_id.append_line_number(token.line_num)
            else:
                self.error_handler.flag(token, 'IDENTIFIER_REDEFINED', self)

            token = self.next_token()
            token = self.synchronize(TypeDefinitionsParser.EQUALS_SET)
            if token.ptype == PascalSpecialSymbol.EQUALS:
                token = self.next_token()
            else:
                self.error_handler.flag(token, 'MISSING_EQUALS', self)

            typespecification_parser = TypeSpecificationParser(self)
            type = typespecification_parser.parse(token)

            if type_id:
                type_id.set_definition(Definition.TYPE)

            if type != None and type_id != None:
                if type.get_identifier() == None:
                    type.set_identifier(type_id)
                type_id.set_typespec(type)
            else:
                token = self.synchronize(TypeDefinitionsParser.FOLLOW_SET)

            token = self.current_token()

            if token.type == TokenType.EOF:
                self.error_handler.flag(token, 'UNEXPECTED_EOF', self)
                return
            if token.value == 'SEMICOLON':
                while token.value == 'SEMICOLON':
                    token = self.next_token()
            elif token.value in TypeDefinitionsParser.IDENTIFIER_SET:
                self.error_handler.flag(token, 'MISSING_SEMICOLON', self)

            token = self.synchronize(self.IDENTIFIER_SET, ptt_set=self.IDENTIFIER_SET_PTT)

        return None


class TypeSpecificationParser(PascalParserTD):
    TYPE_START_SET = copy.deepcopy(ConstantDefinitionsParser.CONSTANT_START_SET)
    TYPE_START_SET.append('LEFT_PAREN')
    TYPE_START_SET.append('COMMA')
    TYPE_START_SET.append('SEMICOLON')
    TYPE_START_SET.append('ARRAY')
    TYPE_START_SET.append('RECORD')
    TYPE_START_SET.append('SEMICOLON')
    TYPE_START_SET_PTT = copy.deepcopy(ConstantDefinitionsParser.CONSTANT_START_SET_PTT)

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        token = self.synchronize(self.TYPE_START_SET, ptt_set=self.TYPE_START_SET_PTT)
        type = token.value
        if type == 'ARRAY':
            array_type_parser = ArrayTypeParser(self)
            return array_type_parser.parse(token)
        elif type == 'RECORD':
            record_type_parser = RecordTypeParser(self)
            return record_type_parser.parse(token)
        else:
            simple_type_parser = SimpleTypeParser(self)
            return simple_type_parser.parse(token)


class SimpleTypeParser(TypeSpecificationParser):
    SIMPLE_TYPE_START_SET = copy.deepcopy(ConstantDefinitionsParser.CONSTANT_START_SET)
    SIMPLE_TYPE_START_SET.append('LEFT_PAREN')
    SIMPLE_TYPE_START_SET.append('COMMA')
    SIMPLE_TYPE_START_SET.append('SEMICOLON')
    SIMPLE_TYPE_START_SET_PTT = copy.deepcopy(ConstantDefinitionsParser.CONSTANT_START_SET_PTT)

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        token = self.synchronize(self.SIMPLE_TYPE_START_SET,ptt_set=self.SIMPLE_TYPE_START_SET_PTT)
        if token.type == TokenType.EOF:
            self.error_handler.flag(token, 'UNEXPECTED_EOF', self)
            return

        if token.ptype == PTT.IDENTIFIER:
            name = token.value.lower()
            id = Parser.symtab_stack.lookup(name)
            if id:
                definition = id.get_definition()
                if definition == Definition.TYPE:
                    id.append_line_number(token.line_num)
                    token = self.next_token()
                    return id.get_typespec()
                elif definition != Definition.CONSTANT and definition != Definition.ENUMERATION_CONSTANT:
                    self.error_handler.flag(token, 'NOT_TYPE_IDENTIFIER', self)
                    token = self.next_token()
                    return None
                else:
                    subrange_parser = SubrangeTypeParser(self)
                    return subrange_parser.parse(token)
            else:
                # id == None
                self.error_handler.flag(token, 'IDENTIFIER_UNDEFINED', self)
                token = self.next_token()
                return None
        elif token.ptype == PascalSpecialSymbol.LEFT_PAREN:
            enumration_parser = EnumerationTypeParser(self)
            return enumration_parser.parse(token)
        elif token.ptype == PTT.RESERVED and (token.value == 'COMMA' or token.value == 'SEMICOLON'):
            self.error_handler.flag(token, 'INVALID_TYPE', self)
            return None
        else:
            subrange_parser = SubrangeTypeParser(self)
            return subrange_parser.parse(token)


class VariableDeclarationsParser(DeclarationsParser):
    IDENTIFIER_SET = copy.deepcopy(DeclarationsParser.VAR_START_SET)
    IDENTIFIER_SET.append('END')
    IDENTIFIER_SET.append('SEMICOLON')
    IDENTIFIER_SET_PTT = [PTT.IDENTIFIER, ]
    NEXT_START_SET = copy.deepcopy(DeclarationsParser.ROUTINE_START_SET)
    NEXT_START_SET.append('IDENTIFIER')
    NEXT_START_SET.append('SEMICOLON')
    IDENTIFIER_START_SET = ['IDENTIFIER', 'COMMA']
    IDENTIFIER_FOLLOW_SET = ['COLON', 'SEMICOLON'] + DeclarationsParser.VAR_START_SET
    COMMA_SET = ['COMMA', 'COLON', 'IDENTIFIER', 'SEMICOLON']
    COLON_SET = ['COLON', 'SEMICOLON']

    def __init__(self, parent):
        self.definition = None
        super().__init__(parent)

    def set_definition(self, definition):
        self.definition = definition

    def parse(self, token, parent_id):
        token = self.synchronize(VariableDeclarationsParser.IDENTIFIER_SET, ptt_set=self.IDENTIFIER_SET_PTT)

        while token.ptype == PTT.IDENTIFIER:
            self.parse_identifier_sublist(token, self.IDENTIFIER_FOLLOW_SET, self.COMMA_SET)
            token = self.current_token()
            if token.type == TokenType.EOF:
                self.error_handler.flag(token, 'UNEXPECTED EOF', self)
                return

            if token.ptype == PascalSpecialSymbol.SEMICOLON:
                while token.ptype == PascalSpecialSymbol.SEMICOLON:
                    token = self.next_token()
            elif token.value in VariableDeclarationsParser.NEXT_START_SET:
                self.error_handler.flag(token, 'MISSING_SEMICOLON', self)

            token = self.synchronize(VariableDeclarationsParser.IDENTIFIER_SET, ptt_set=VariableDeclarationsParser.IDENTIFIER_SET_PTT)

        return None

    def parse_identifier_sublist(self, token, follow_set, comma_set, ptt_set=[]):
        sublist = []
        first = True

        while self.sublist_loop(token, first, follow_set):
            first = False
            token = self.synchronize(VariableDeclarationsParser.IDENTIFIER_SET, ptt_set=VariableDeclarationsParser.IDENTIFIER_SET_PTT)
            id = self.parse_identifier(token)
            if id:
                sublist.append(id)

            token = self.synchronize(comma_set, ptt_set=ptt_set)

            if token.ptype == PascalSpecialSymbol.COMMA:
                token = self.next_token()

                if token.value in follow_set:
                    self.error_handler.flag(token, 'MISSING_IDENTIFIER', self)
            elif token.value in VariableDeclarationsParser.IDENTIFIER_START_SET:
                self.error_handler.flag(token, 'MISSING_COMMA', self)

        if self.definition != Definition.PROGRAM_PARM:
            type = self.parse_typespec(token)
            for e in sublist:
                e.set_typespec(type)

        return sublist

    def sublist_loop(self, token, first, follow_set):
        """
        最初の一回とTokenの状況でループするかどうかの判断を行う。
        """
        if first:
            return True
        if token.value in follow_set:
            return False
        else:
            return True

    def parse_identifier(self, token):
        id = None
        if token.ptype == PTT.IDENTIFIER:
            name = token.value
            id = Parser.symtab_stack.lookup_local(name)
            if not id:
                id = Parser.symtab_stack.enter_local(name)
                id.set_definition(self.definition)
                id.append_line_number(token.line_num)
            else:
                self.error_handler.flag(token, 'IDENTIFIER_REDEFINED', self)

            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_IDENTIFIER', self)

        return id

    def parse_typespec(self, token):
        token = self.synchronize(VariableDeclarationsParser.COLON_SET)
        if token.ptype == PascalSpecialSymbol.COLON:
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_COLON', self)

        typespec_parser = TypeSpecificationParser(self)
        type = typespec_parser.parse(token)

        if self.definition == Definition.VARIABLE and self.definition == Definition.FIELD and type and (not type.get_identifier()):
            self.error_handler.flag(token, 'INVALID_TYPE', self)

        return type

    def set_definition(self, definitation):
        self.definition = definitation


class RecordTypeParser(TypeSpecificationParser):
    END_SET = copy.deepcopy(DeclarationsParser.VAR_START_SET)
    END_SET.append('END')
    END_SET.append('SEMICOLON')

    def __init__(self, parent):
        self.definition = None
        super().__init__(parent)

    def parse(self, token):
        record_type = TypeSpec(TypeForm.RECORD)
        token = self.next_token()
        record_type.set_attribute('RECORD_SYMTAB', Parser.symtab_stack.push(None))

        var_decl_parser = VariableDeclarationsParser(self)
        var_decl_parser.set_definition(Definition.FIELD)
        var_decl_parser.parse(token, None)

        Parser.symtab_stack.pop()

        token = self.synchronize(self.END_SET)
        if token.ptype == PTT.RESERVED and token.value == 'END':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_END', self)

        return record_type


class SubrangeTypeParser(TypeSpecificationParser):
    def __init__(self, parent):
        self.definition = None
        super().__init__(parent)

    # SubrangeTypeParser
    def parse(self, token):
        subrange_type = TypeSpec(TypeForm.SUBRANGE)
        min_val = None
        max_val = None

        constant_token = copy.copy(token)
        constant_parser = ConstantDefinitionsParser(self)
        min_val = constant_parser.parse_constant(token)

        if constant_token.ptype == PTT.IDENTIFIER:
            min_type = constant_parser.get_constant_type_token(constant_token)
        else:
            min_type = constant_parser.get_constant_type_value(min_val)
        min_val = self.check_value_type(constant_token, min_val, min_type)

        token = self.current_token()
        saw_dot_dot = False

        if token.value == 'DOT_DOT':
            token = self.next_token()
            saw_dot_dot = True

        if token.ptype == PTT.IDENTIFIER or token.ptype == PTT.STRING or token.ptype == PTT.INTEGER or token.value in ConstantDefinitionsParser.CONSTANT_START_SET:
            if not saw_dot_dot:
                self.error_handler.flag(token, 'MISSING_DOT_DOT', self)
            token = self.synchronize(ConstantDefinitionsParser.CONSTANT_START_SET, ptt_set=ConstantDefinitionsParser.CONSTANT_START_SET_PTT)
            constant_token = copy.copy(token)
            max_val = constant_parser.parse_constant(token)

            if constant_token.ptype == PTT.IDENTIFIER:
                max_type = constant_parser.get_constant_type_token(constant_token)
            else:
                max_type = constant_parser.get_constant_type_value(max_val)

            max_val = self.check_value_type(constant_token, max_val, max_type)

            if min_type == None or max_type == None:
                self.error_handler.flag(token, 'INVALID_SUBRANGE_TYPE', self)
            elif min_type != max_type:
                self.error_handler.flag(token, 'INVALID_SUBRANGE_TYPE', self)
            elif min_val != None and max_val != None and min_val >= max_val:
                self.error_handler.flag(token, 'MIN_GT_MAX', self)
        else:
            self.error_handler.flag(token, 'MIN_GT_MAX', self)

        subrange_type.set_attribute('SUBRANGE_BASE_TYPE', min_type)
        subrange_type.set_attribute('SUBRANGE_MIN_VALUE', min_val)
        subrange_type.set_attribute('SUBRANGE_MAX_VALUE', max_val)

        return subrange_type

    def check_value_type(self, token,  val, type):
        if type == None:
            return val
        if type == Predefined.integer_type:
            return val
        elif type == Predefined.char_type:
            ch = val[0]
            return ord(ch)
        elif type.get_form() == TypeForm.ENUMERATION:
            return val
        else:
            self.error_handler.flag(token, 'INVALID_SUBRANGE_TYPE', self)
            return val


class EnumerationTypeParser(TypeSpecificationParser):
    ENUM_CONSTANT_START_SET = ['IDENTIFIER', 'COMMA']
    ENUM_DEFINITION_FOLLOW_SET = ['RIGHT_PAREN', 'SEMICOLON'] + DeclarationsParser.VAR_START_SET

    def __init__(self, parent):
        self.definition = None
        super().__init__(parent)

    def parse(self, token):
        enum_type = TypeSpec(TypeForm.ENUMERATION)
        value = -1
        constants = []

        token = self.next_token()
        first = True

        while self.enum_loop(token, first):
            first = False
            token = self.synchronize(self.ENUM_CONSTANT_START_SET)
            value += 1
            self.parse_enum_identifier(token, value, enum_type, constants)
            token = self.current_token()

            if token.ptype == PascalSpecialSymbol.COMMA:
                token = self.next_token()

                if token.value in self.ENUM_DEFINITION_FOLLOW_SET:
                    self.error_handler.flag(token, 'MISSING_IDENTIFIER', self)
#            elif token.value in self.ENUM_CONSTANT_START_SET:
            elif token.ptype == PTT.IDENTIFIER:
                self.error_handler.flag(token, 'MISSING_COMMA', self)

        if token.ptype == PascalSpecialSymbol.RIGHT_PAREN:
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'ENUMERATION_CONSTANTS', self)

        enum_type.set_attribute(Definition.ENUMERATION_CONSTANT, constants)
        return enum_type

    def enum_loop(self, token, first):
        if first:
            return True
        if token.value in self.ENUM_DEFINITION_FOLLOW_SET:
            return False
        else:
            return True

    def parse_enum_identifier(self, token, value, enum_type, constants):
        if token.ptype == PTT.IDENTIFIER:
            name = token.value.lower()
            const_id = Parser.symtab_stack.lookup_local(name)

            if const_id:
                self.error_handler.flag(token, 'IDENTIFIER_REDEFINED', self)
            else:
                const_id = Parser.symtab_stack.enter_local(name)
                const_id.set_definition(Definition.ENUMERATION_CONSTANT)
                const_id.set_typespec(enum_type)
                const_id.set_attribute('CONSTANT_VALUE', value)
                const_id.append_line_number(token.line_num)
                constants.append(const_id)
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_IDENTIFIER', self)

class ArrayTypeParser(TypeSpecificationParser):
    LEFT_BRACKET_SET = copy.deepcopy(SimpleTypeParser.SIMPLE_TYPE_START_SET)
    LEFT_BRACKET_SET.append('LEFT_BRACKET')
    LEFT_BRACKET_SET.append('RIGHT_BRACKET')
    LEFT_BRACKET_SET_PTT = copy.deepcopy(SimpleTypeParser.SIMPLE_TYPE_START_SET_PTT)
    RIGHT_BRACKET_SET = ['RIGHT_BRACKET', 'OF', 'SEMICOLON']
    OF_SET = copy.deepcopy(TypeSpecificationParser.TYPE_START_SET)
    OF_SET.append('OF')
    OF_SET.append('SEMICOLON')
    INDEX_START_SET = copy.deepcopy(SimpleTypeParser.SIMPLE_TYPE_START_SET)
    INDEX_START_SET.append('COMMA')
    INDEX_START_SET_PTT = copy.deepcopy(SimpleTypeParser.SIMPLE_TYPE_START_SET_PTT)
    INDEX_END_SET = ['RIGHT_BRACKET', 'OF', 'SEMICOLON']
    INDEX_FOLLOW_SET = copy.deepcopy(INDEX_START_SET) + INDEX_END_SET

    def __init__(self, parent):
        self.definition = None
        super().__init__(parent)

    def parse(self, token):
        # ARRAY
        array_type = TypeSpec(TypeForm.ARRAY)
        token = self.next_token()

        token = self.synchronize(self.LEFT_BRACKET_SET, ptt_set=self.LEFT_BRACKET_SET_PTT)
        if token.value != 'LEFT_BRACKET':
            self.error_handler.flag(tokne, 'MISSING_LEFT_BRACKET', self)

        element_type = self.parse_index_type_list(token, array_type)
        token = self.synchronize(self.RIGHT_BRACKET_SET)
        if token.ptype == PascalSpecialSymbol.RIGHT_BRACKET:
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_RIGHT_BRACKET', self)

        token = self.synchronize(self.OF_SET)
        if token.ptype == PTT.RESERVED and token.value == 'OF':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_OF', self)

        element_type.set_attribute('ARRAY_ELEMENT_TYPE', self.parse_element_type(token))
        return array_type


    def parse_index_type_list(self, token, array_type):
        element_type =  array_type
        another_index = False
        token = self.next_token()
        first  = True

        while first or another_index:
            first = False
            another_index = False

            token = self.synchronize(self.INDEX_START_SET, ptt_set=self.INDEX_START_SET_PTT)
            self.parse_index_type(token, element_type)

            token = self.synchronize(self.INDEX_FOLLOW_SET)
            if token.value != 'COMMA' and token.value == 'RIGHT_BRACKET':
                if token.value in self.INDEX_START_SET:
                    self.error_handler.flag(token, 'MISSING_COMMA', self)
                    another_index = True
            elif token.value == 'COMMA':
                new_element_type = TypeSpec(TypeForm.ARRAY)
                element_type.set_attribute('ARRAY_ELEMENT_TYPE', new_element_type)
                element_type = new_element_type

                token = self.next_token()
                another_index = True

        return element_type


    def parse_index_type(self, token, array_type):
        simple_parser = SimpleTypeParser(self)
        index_type = simple_parser.parse(token)
        array_type.set_attribute('ARRAY_INDEX_TYPE', index_type)

        if not index_type:
            return

        form = index_type.get_form()
        count = 0

        if form == TypeForm.SUBRANGE:
            min_val = index_type.get_attribute('SUBRANGE_MIN_VALUE')
            max_val = index_type.get_attribute('SUBRANGE_MAX_VALUE')

            if min_val != None and max_val != None:
                count = max_val - min_val
        elif form == TypeForm.ENUMERATION:
            constants = index_type.get_attribute(Definition.ENUMERATION_CONSTANT)
            count = len(constants)
        else:
            self.error_handler.flag(token, 'INVALID_INDEX_TYPE', self)
        array_type.set_attribute('ARRAY_ELEMENT_COUNT', count)

    def parse_element_type(self, token):
        typespec_parser = TypeSpecificationParser(self)
        return typespec_parser.parse(token)



def set_line_number(node, token):
    if node:
        node.set_attribute('LINE', token.line_num)


def get_content_type(value):
    if isinstance(value, Token):
        name = value.value.lower()
        id = Parser.symtab_stack.lookup(name)
        if not id:
            return None

        defination = id.get_definition()
        if defination == Definition.CONSTANT or defination == Definition.ENUMERATION_CONSTANT:
            return id.get_typespec()
        return None

    else:
        content_type = None
        if isinstance(value, int):
            content_type = Predefined.integer_type
        elif isinstance(value, float):
            content_type = Predefined.real_type
        elif isinstance(value, str):
            if len(value) == 1:
                content_type = Predefined.char_type
            else:
                content_type = TypeSpec(value)
        return content_type
