# -*- coding: utf-8 -*-
import sys
import copy

from limbus_core.message import Message, MessageType ,MessageListener
from limbus_core.frontend.parser import Parser
from limbus_core.intermidiate.iCode_factory import iCodeFactory, iCodeNodeFactory
from limbus_core.intermidiate.type_impl import Predefined, Definition, TypeSpec, TypeForm
from limbus_core.intermidiate.symtabstack_impl import SymTabKey

from pascal.pascal_error import PascalErrorType, PascalError
from pascal.pascal_token import *
from pascal.pascal_parser import *


class PascalErrorHandler:
    def __init__(self):
        self.MAX_ERROR = 25
        self.error_cnt = 0

    def flag(self, token, error_code, parser):
        line = parser.get_line()
        msg = Message(MessageType.SYNTAX_ERROR, (token, error_code, line))
        parser.send_message(msg)

        self.error_cnt = self.error_cnt + 1
        if self.error_cnt > self.MAX_ERROR:
            self.abort_translation('TOO_MANY_ERRORS', parser)

    def abort_translation(self, err_code, parser):
        msg = Message(MessageType.SYNTAX_ERROR, "FATAL_ERROR:"+err_code)
        parser.send_message(msg)
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
        self.predefined.initialize(Parser.symtab_stack)
        self.routine_id = Parser.symtab_stack.enter_local('dummy_program_name')
        self.routine_id.set_definition(Definition.PROGRAM)
        Parser.symtab_stack.set_program_id(self.routine_id)

        self.routine_id.set_attribute(SymTabKey.ROUTINE_SYMTAB, Parser.symtab_stack.push(None))
        self.routine_id.set_attribute(SymTabKey.ROUTINE_ICODE, Parser.iCode)

        block_parser = BlockParser(self)

        try:
            token = self.next_token()
            root_node = block_parser.parse(token, self.routine_id)

            if root_node == None:
                self.error_handler.abort_translation('PARSE_ERROR', self)
                return

            Parser.iCode.set_root(root_node)
            Parser.symtab_stack.pop()

            token = self.current_token()
            if token.ptype == PTT.RESERVED and token.value == 'DOT':
                self.error_handler.flag(token, 'MISSING_PERIOD', self)
            token = self.current_token()

            line_number = token.line_num
            err_cnt = self.get_error_count()

            msg = Message(MessageType.PARSER_SUMMARY, (line_number, err_cnt))
            self.send_message(msg)

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

    def synchronize(self, syncset, ptt_set = []):
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

        declaration_parser.parse(token)

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

    def parse(self, token):
        token = self.synchronize(DeclarationsParser.DECLARATION_START_SET)
        if token.ptype == PTT.RESERVED and token.value == 'CONST':
            token = self.next_token()
            constant_definition_parser = ConstantDefinitionsParser(self)
            constant_definition_parser.parse(token)

        token = self.synchronize(self.TYPE_START_SET)
        if token.ptype == PTT.RESERVED and token.value == 'TYPE':
            token = self.next_token()
            type_defination_parser = TypeDefinitionsParser(self)
            type_defination_parser.parse(token)

        token = self.synchronize(self.VAR_START_SET)

        if token.ptype == PTT.RESERVED and token.value == 'VAR':
            token = self.next_token()
            variable_declarations_parser = VariableDeclarationsParser(self)
            variable_declarations_parser.set_definition(Definition.VARIABLE)
            variable_declarations_parser.parse(token)

        token = self.synchronize(DeclarationsParser.ROUTINE_START_SET)


class StatementParser(PascalParserTD):
    STMT_START_SET = ['BEGIN', 'CASE', 'FOR', 'IF', 'REPEAT', 'WHILE', 'IDENTIFIER', 'SEMICOLON']
    STMT_FOLLOW_SET = ['SEMICOLON', 'END', 'ELSE', 'UNTIL', 'DOT']

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        if token.ptype == PTT.RESERVED and  token.value == 'BEGIN':
            statement_node = CompoundStatementParser(self).parse(token)
        elif token.ptype == PTT.IDENTIFIER:
            statement_node = AssignmentStatementParser(self).parse(token)
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


class AssignmentStatementParser(StatementParser):
    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        assigin_node = iCodeNodeFactory().create('ASSIGN')
        target_name = token.value.lower()
        target_id = Parser.symtab_stack.lookup(target_name)
        if not target_id:
            target_id = Parser.symtab_stack.enter_local(target_name)

        # print("parse ", target_name, " id:", target_id, " ")

        target_id.append_line_number(token.line_num)
        token = self.next_token()
        variable_node = iCodeNodeFactory().create('VARIABLE')
        variable_node.set_attribute('ID', target_id)

        assigin_node.add_child(variable_node)

        if token.value == 'COLON_EQUALS':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_COLON_EQUALS', self)

        expression_parser = ExpressionParser(self)
        assigin_node.add_child(expression_parser.parse(token))

        return assigin_node


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
        token = self.current_token()
        token_type = token.value

        if token_type in self.op_map:
            node_type = self.op_map[token_type]
            opnode = iCodeNodeFactory().create(node_type)
            opnode.add_child(root_node)

            token = self.next_token()
            opnode.add_child(self.parse_simple_expression(token))
            root_node = opnode

        return root_node

    def parse_simple_expression(self, token):
        sign_type = None

        token_type = token.value
        if token_type == 'PLUS' or token_type == 'MINUS':
            sign_type = token_type
            token = self.next_token()

        root_node = self.parse_term(token)

        if sign_type == 'MINUS':
            negate_node = iCodeNodeFactory().create('NEGATE')
            negate_node.add_child(root_node)
            root_node = negate_node

        token = self.current_token()
        token_type = token.value

        while token_type in self.add_ops:
            node_type = self.op_map[token_type]
            op_node = iCodeNodeFactory().create(node_type)
            op_node.add_child(root_node)

            token = self.next_token()
            op_node.add_child(self.parse_term(token))

            root_node = op_node
            token = self.current_token()
            token_type = token.value

        return root_node

    def parse_term(self, token):
        root_node = self.parse_factor(token)
        token = self.current_token()
        token_type = token.value

        while token_type in self.mul_ops:
            node_type = self.op_map[token_type]
            op_node = iCodeNodeFactory().create(node_type)
            op_node.add_child(root_node)

            token = self.next_token()
            op_node.add_child(self.parse_factor(token))

            root_node = op_node

            token = self.current_token()
            token_type = token.value

        return root_node

    def parse_factor(self, token):
        ptype = token.ptype
        root_node = None
        if ptype == PTT.IDENTIFIER:
            name = token.value.lower()
            id = Parser.symtab_stack.lookup(name)
            if not id:
                self.error_handler.flag(token, 'IDENTIFIER_UNDEFINED', self)
                id = Parser.symtab_stack.enter_local(name)

            root_node = iCodeNodeFactory().create('VARIABLE')
            root_node.set_attribute('ID', id)
            id.append_line_number(token.line_num)
            token = self.next_token()

        elif ptype == PTT.INTEGER:
            root_node = iCodeNodeFactory().create('INTEGER_CONSTANT')
            root_node.set_attribute('VALUE', token.value)
            token = self.next_token()

        elif ptype == PTT.REAL:
            root_node = iCodeNodeFactory().create('REAL_CONSTANT')
            root_node.set_attribute('VALUE', token.value)
            token = self.next_token()

        elif ptype == PTT.STRING:
            root_node = iCodeNodeFactory().create('STRING_CONSTANT')
            root_node.set_attribute('VALUE', token.value)
            token = self.next_token()

        elif token.value == 'NOT':
            token = self.next_token()
            root_node = iCodeNodeFactory().create('NOT')
            root_node.set_attributes(self.parser_factor(token))

        elif token.value == 'LEFT_PAREN':
            token = self.next_token()
            root_node = self.parse_expression(token)

            token = self.current_token()
            if token.value == 'RIGHT_PAREN':
                token = self.next_token()
            else:
                self.error_handler.flag(token, 'MISSING_RIGHT_PAREN', self)

        else:
            self.error_handler.flag(token, 'UNEXPECTED_TOKEN', self)

        return root_node


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
        select_node.add_child(expression_parser.parse(token))

        token = self.synchronize(self.OF_SET)
        if token.value == 'OF':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_OF', self)

        constain_set = []
        while token.type != TokenType.EOF and token.value != 'END':
            select_node.add_child(self. parse_branch(token, constain_set))
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

    def parse_branch(self, token, constant_set):
        branch_node = iCodeNodeFactory().create('SELECT_BRANCH')
        constants_node = iCodeNodeFactory().create('SELECT_CONSTANTS')
        branch_node.add_child(constants_node)

        self.parse_constant_list(token, constants_node, constant_set)
        token = self.current_token()

        if token.value == 'COLON':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_COLON', self)

        statement_parser = StatementParser(self)
        branch_node.add_child(statement_parser.parse(token))

        return branch_node

    def parse_constant_list(self, token, constants_node, constants_set):
        while token.value in self.CONSTANT_START_SET or token.ptype in self.CONSTANT_START_SET_PTT:
            constants_node.add_child(self.parse_constant(token, constants_set))
            token = self.synchronize(self.COMMA_SET)

            if token.value == 'COMMA':
                token = self.next_token()
            elif token.value in self.CONSTANT_START_SET:
                self.error_handler.flag(token, 'MISSING_COMMA', self)

    def parse_constant(self, token, constants_set):
        sign = None
        constant_node = None

        token = self.synchronize(self.CONSTANT_START_SET, ptt_set = self.CONSTANT_START_SET_PTT)
        token_type = token.value

        if token_type == 'PLUS' or token_type == 'MINUS':
            sign = token_type
            token = self.next_token()

        if token.ptype == PTT.IDENTIFIER:
            constant_node = self.parse_identifier_constant(token, sign)
        elif token.ptype == PTT.INTEGER:
            constant_node = self.parse_integer_constant(token.text, sign)
        elif token.ptype == PTT.STRING:
            constant_node = self.parse_character_constant(token, token.value, sign)
        else:
            self.error_handler.flag(token, 'INVALID_CONSTANT', self)

        if constant_node != None:
            value = constant_node.get_attribute('VALUE')
            if value in constants_set:
                self.error_handler.flag(token, 'CASE_CONSTANT_REUSED', self)
            else:
                constants_set.append(value)

        token = self.next_token()
        return constant_node

    def parse_identifier_constant(self, token, sign):
        self.error_handler.flag(token, 'INVALID_CONSTANT', self)
        return None

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

        set_line_number(init_assign_node, token)

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

        control_var_node = init_assign_node.get_children()[0]
        rel_op_node.add_child(control_var_node)

        expression_parser = ExpressionParser(self)
        rel_op_node.add_child(expression_parser.parse(token))

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
        next_assign_node.add_child(control_var_node)

        if direction == 'TO':
            arith_op_node = iCodeNodeFactory().create('ADD')
        else:
            arith_op_node = iCodeNodeFactory().create('SUBTRACT')

        arith_op_node.add_child(control_var_node)
        one_node = iCodeNodeFactory().create('INTEGER_CONSTANT')
        one_node.set_attribute('VALUE', 1)
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
        if_node.add_child(expression_parser.parse(token))

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
        test_node.add_child(express_parser.parse(token))
        loop_node.add_child(test_node)

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
        not_node.add_child(expression_parser.parse(token))

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

    def parse(self, token):
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
            tokne = self.next_token()
            if sign == 'MINUS':
                return -value
            else:
                return value
        elif token.ptype == PTT.STRING:
            if sign:
                self.error_handler.flag(token, 'INVALID_CONSTANT', self)
            token = self.next_token()
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
    EQUALS_SET = copy.deepcopy(ConstantDefinitionsParser.CONSTANT_START_SET)
    EQUALS_SET.append('EQUALS')
    EQUALS_SET.append('SEMICOLON')
    FOLLOW_SET = ['SEMICOLON']
    NEXT_START_SET = copy.deepcopy(DeclarationsParser.VAR_START_SET)
    NEXT_START_SET.append('SEMICOLON')
    NEXT_START_SET.append('IDENTIFIER')

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        token = self.synchronize(TypeDefinitionsParser.IDENTIFIER_SET)

        while token.ptype == PTT.RESERVED and token.value == 'IDENTIFIER':
            name = token.value.lower()
            type_id = Parser.symtab_stack.lookup(name)

            if not type_id:
                type_id = Parser.symtab_stack.enter_local(name)
                type_id.append_line_number(token.line_num)
            else:
                self.error_handler.flag(token, 'IDENTIFIER_REDEFINED', self)

            token = self.next_token()
            token = self.synchronize(TypeDefinitionsParser.EQUALS_SET)
            if token.ptype == PTT.RESERVED and token.value == 'EQUALS':
                token = self.next_token()
            else:
                self.error_handler.flag(token, 'MISSING_EQUALS', self)

            typespecification_parser = TypeSpecificationParser(self)
            type = typespecification_parser.parse(token)

            if type_id:
                type_id.set_definition(type)

            if type != None and type_id != None:
                if type.get_identifier() == None:
                    type.set_identifier(type_id)
                type_id.set_identifier(type)
            else:
                token = self.synchronize(TypeDefinitionsParser.FOLLOW_SET)

            token = self.curretnt_token()
            token_type = token.get_type()

            if token.ptype == PTT.RESERVED and token.value == 'SEMICOLON':
                while token.get_type() != 'SEMICOLON':
                    token = self.next_token()
            elif token_type in TypeDefinitionsParser.IDENTIFIER_SET:
                self.error_handler.flag(token, 'MISSING_SEMICOLON', self)


class TypeSpecificationParser(PascalParserTD):
    TYPE_START_SET = copy.deepcopy(ConstantDefinitionsParser.CONSTANT_START_SET)
    TYPE_START_SET.append('LEFT_PAREN')
    TYPE_START_SET.append('COMMA')
    TYPE_START_SET.append('SEMICOLON')
    TYPE_START_SET.append('ARRAY')
    TYPE_START_SET.append('RECORD')
    TYPE_START_SET.append('SEMICOLON')


    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        token = self.synchronize(TypeDefinitionsParser.TYPE_START_SET)
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

    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        token = self.synchronize(SimpleTypeParser.SIMPLE_TYPE_START_SET)
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
        elif token.ptype == PTT.RESERVED and token.value == 'LEFT_PAREN':
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
    IDENTIFIER_SET.append('IDENTIFIER')
    IDENTIFIER_SET.append('END')
    IDENTIFIER_SET.append('SEMICOLON')
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

    def parse(self, token):
        token = self.synchronize(VariableDeclarationsParser.IDENTIFIER_SET)

        while token.ptype == PTT.IDENTIFIER:
            self.parse_identifier_sublist(token)
            token = self.current_token()
            if token.type == TokenType.EOF:
                self.error_handler.flag(token, 'UNEXPECTED EOF', self)
                return


            if token.ptype == PTT.RESERVED and token.value == 'SEMICOLON':
                while token.ptype == PTT.RESERVED and token.value == 'SEMICOLON':
                    token = self.next_token()
            elif token.value in VariableDeclarationsParser.NEXT_START_SET:
                self.error_handler.flag(token, 'MISSING_SEMICOLON', self)

            token = self.synchronize(VariableDeclarationsParser.IDENTIFIER_SET)
                
    def parse_identifier_sublist(self, token):
        sublist = []
        first = True

        while self.sublist_loop(token, first):
            first = False
            token = self.synchronize(VariableDeclarationsParser.IDENTIFIER_SET)
            id = self.parse_identifier(token)
            if id:
                sublist.append(id)

            token = self.synchronize(VariableDeclarationsParser.COMMA_SET)

            if token.ptype == PTT.RESERVED and token.value == 'COMMA':
                token = self.next_token()

                if token.value in VariableDeclarationsParser.IDENTIFIER_FOLLOW_SET:
                    self.error_handler.flag(token, 'MISSING_IDENTIFIER', self)
            elif token.value in VariableDeclarationsParser.IDENTIFIER_START_SET:
                self.error_handler.flag(token, 'MISSING_COMMA', self)

        type = self.parse_typespec(token)
        for e in sublist:
            e.set_typespec(type)

        return sublist

    def sublist_loop(self, token, first):
        """
        最初の一回とTokenの状況でループするかどうかの判断を行う。
        """
        if first:
            return True
        if token.value in VariableDeclarationsParser.IDENTIFIER_SET:
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
        if token.ptype == PTT.RESERVED and token.value == 'COLON':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_COLON', self)

        typespec_parser = TypeSpecificationParser(self)
        type = typespec_parser.parse(token)

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
        record_type = TypeSpec('RECORD')
        token = self.next_token()
        record_type.set_attribute(TypeKey.RECORD_SYMTAB, Parser.symtab_stack.push(None))

        var_decl_parser = VariableDeclarationsParser(self)
        var_decl_parser.set_definition(Definition.FIELD)
        var_decl_parser.parse(token)

        Parser.symtab_stack.pop()

        token = self.synchronize(self.END_SET)
        if token.ptype == PTT.RESERVED and token.value == 'END':
            token = self.next_token()
        else:
            self.error_handler.falg(token, 'MISSING_END', self)

        return record_type

class SubrangeTypeParser(TypeSpecificationParser):
    def __init__(self, parent):
        self.definition = None
        super().__init__(parent)

    def parse(self, token):
        subrange_type = TypeSpec('SUBRANGE')
        min_val = None
        max_val = None

        constant_token = copy.deepcopy(token)
        constant_parser = ConstantDefinitionsParser(self)
        min_val = constant_parser.parse_constant(token)

        if constant_token.ptype == PTT.IDENTIFIER:
            min_type = constant_parser.get_constant_type(constant_token)
        else:
            min_type = constant_parser.get_constant_type(min_val)
        min_val = self.check_value_type(constant_token, min_val, min_type)

        token = self.current_token()
        saw_dot_dot = False

        if token.ptype == PTT.IDENTIFIER and token.value == 'DOT_DOT':
            token = self.next_token()
            saw_dot_dot = True

        token_type = token.get_type()

        if token_type in ConstantDefinitionsParser.CONSTANT_START_SET:
            if not saw_dot_dot:
                self.error_handler.flag(token, 'MISSING_DOT_DOT', self)
            token = self.synchronize(ConstantDefinitionsParser.CONSTANT_START_SET)
            constant_token = copy.deepcopy(token)
            max_val = constant_parser.parse_constant(token)

            if constant_token.ptype == PTT.IDENTIFIER:
                max_type = constant_parser.get_constant_type(constant_token)
            else:
                max_type = constant_parser.get_constant_type(max_val)

            max_val = self.check_value_type(constant_token, max_val, max_type)

            if min_type == None or max_type == None:
                self.error_handler.flag(token, 'INVALID_SUBRANGE_TYPE', self)
            elif min_type != max_type:
                self.error_handler.flag(token, 'INVALID_SUBRANGE_TYPE', self)
            elif min_val != None and max_val != None and min_val >= max_val:
                self.error_handler.flag(token, 'MIN_GT_MAX', self)
        else:
            self.error_handler.flag(token, 'MIN_GT_MAX', self)

        subrange_type.set_attribute(TypeKey.SUBRANGE_BASE_TYPE, min_type)
        subrange_type.set_attribute(TypeKey.SUBRANGE_MIN_VALUE, min_val)
        subrange_type.set_attribute(TypeKey.SUBRANGE_MAX_VALUE, max_type)

        return subrange_type

    def check_value_type(self, val, type):
        if type == None:
            return val
        if type == Predefined.integer_type:
            return val
        elif type == Predefined.char_type:
            ch = val[0]
            return int(ch)
        elif type.get_form() == TypeForm.ENUMERATION:
            return value
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
        enum_type = TypeSpec('ENUMERATION')
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

            if token.ptype == PTT.RESERVED and token.value == 'COMMA':
                token = self.next_token()

                if token.get_type() in self.ENUM_DEFINITION_FOLLOW_SET:
                    self.error_handler.flag(token, 'MISSING_IDENTIFIER', self)
            else:
                self.error_handler.flag(token, 'MISSING_COMMA', self)

        if token.ptype == PTT.RESERVED and token.value == 'RIGHT_PAREN':
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'ENUMERATION_CONSTANTS', self)

        enum_type.add_attribute(Definition.ENUMERATION_CONSTANT, constants)
        return enum_type

    def enum_loop(self, token, first):
        if first:
            return True
        if token.get_value() in self.ENUM_CONSTANT_START_SET:
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
                const_id,set_definition(Definition.ENUMERATION_CONSTANT)
                const_id.set_typespec(enum_type)
                const_id.set_attribute('CONSTANT_VALUE', value)
                const_id.append_line_number(token.line_num)
                constants.add(const_id)
            token = self.next_token()
        else:
            self.error_handler.flag(token, 'MISSING_IDENTIFIER', self)

class ArrayTypeParser(TypeSpecificationParser):
    LEFT_BRACKET_SET = copy.deepcopy(SimpleTypeParser.SIMPLE_TYPE_START_SET)
    LEFT_BRACKET_SET.append('LEFT_BRACKET')
    LEFT_BRACKET_SET.append('RIGHT_BRACKET')
    RIGHT_BRACKET_SET = ['RIGHT_BRACKET', 'OF', 'SEMICOLON']
    OF_SET = copy.deepcopy(TypeSpecificationParser.TYPE_START_SET)
    OF_SET.append('OF')
    OF_SET.append('SEMICOLON')
    INDEX_START_SET = copy.deepcopy(SimpleTypeParser.SIMPLE_TYPE_START_SET)
    INDEX_START_SET.append('COMMA')
    INDEX_END_SET = ['RIGHT_BRACKET', 'OF', 'SEMICOLON']
    INDEX_FOLLOW_SET = copy.deepcopy(INDEX_START_SET) + INDEX_END_SET

    def __init__(self, parent):
        self.definition = None
        super().__init__(parent)

    def parse(self, token):
        array_type = TypeSpec('ARRAY')
        token = self.next_token()

        token = self.synchronize(self.LEFT_BRACKET_SET)
        if token.value != 'LEFT_BRACKET':
            self.error_handler.flag(tokne, 'MISSING_LEFT_BRACKET', self)

        element_type = self.parse_index_type_list(token, array_type)
        token = self.synchronize(self.RIGHT_BRACKET_SET)
        if token.ptype == PTT.RESERVED and token.value == 'RIGHT_BRACKET':
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

            token = self.synchronize(self.INDEX_START_SET)
            self.parse_element_type(token)

            token = self.synchronize(self.INDEX_FOLLOW_SET)
            if token.value != 'COMMA' and token.value == 'RIGHT_BRACKET':
                if token.value in self.INDEX_START_SET:
                    self.error_handler.flag(token, 'MISSING_COMMA', self)
                    another_index = True
            elif token.value == 'COMMA':
                new_element_type = TypeSpec('ARRAY')
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
            constants = index_type.get_attribute('ENUMERATION_CONSTANTS')
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
