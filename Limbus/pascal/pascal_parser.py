# -*- coding: utf-8 -*-
import sys
import copy

from limbus_core.message import Message, MessageType ,MessageListener
from limbus_core.frontend.parser import Parser
from limbus_core.intermidiate.iCode_factory import iCodeFactory, iCodeNodeFactory

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
        if isinstance(scanner, Parser):
            super().__init__(scanner.get_scanner())
        else:
            super().__init__(scanner)

        self.iCode = iCodeFactory().create()

    def parse(self):
        token = self.next_token()
        root_node = None

        if token.ptype == PTT.RESERVED and token.value == 'BEGIN':
            statement_parser = StatementParser(self)
            root_node = statement_parser.parse(token)
            token = self.current_token()
        else:
            self.error_handler.flag(token, 'MISSING BEGIN', self)
            token = self.current_token()

        token = self.current_token()
        if token.value != 'DOT':
            self.error_handler.flag(token, 'MISSING_PERIOD', self)

        if root_node:
            self.iCode.set_root(root_node)

        line_number = token.line_num
        err_cnt = self.get_error_count()

        msg = Message(MessageType.PARSER_SUMMARY, (line_number, err_cnt))
        self.send_message(msg)

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

    # CaseStatementParser
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
        rel_op_node.add_child(copy.deepcopy(compound_node))

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
        next_assign_node.add_child(copy.deepcopy(compound_node))

        if direction == 'TO':
            arith_op_node = iCodeNodeFactory().create('ADD')
        else:
            arith_op_node = iCodeNodeFactory().create('SUBTRACT')

        arith_op_node.add_child(copy.deepcopy(control_var_node))
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
            if_node = if_node.add_child(statement_parser.parse(token))

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

def set_line_number(node, token):
    if node:
        node.set_attribute('LINE', token.line_num)
