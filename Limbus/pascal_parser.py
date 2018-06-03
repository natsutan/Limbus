# -*- coding: utf-8 -*-
import sys

from limbus_core.message import Message, MessageType ,MessageListener
from limbus_core.frontend.parser import Parser
from limbus_core.intermidiate.iCode_factory import iCodeFactory, iCodeNodeFactory

from pascal_error import PascalErrorType, PascalError
from pascal_token import *
from pascal_parser import *

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


class StatementParser(PascalParserTD):
    def __init__(self, parent):
        super().__init__(parent)

    def parse(self, token):
        if token.ptype == PTT.RESERVED and  token.value == 'BEGIN':
            statement_node = CompoundStatementParser(self).parse(token)
        elif token.ptype == PTT.IDENTIFIER:
            statement_node = AssignmentStatementParser(self).parse(token)
        else:
            statement_node = iCodeNodeFactory().create('NO_OP')

        set_line_number(statement_node, token)
        return statement_node

    def parse_list(self, token, parent_node, terminator, err_code):

        while token.type != TokenType.EOF and token.value != terminator:
            statement_node = self.parse(token)
            parent_node.add_child(statement_node)

            token = self.current_token()

            if token.value == 'SEMICOLON':
                token = self.next_token()
            elif token.ptype == PTT.IDENTIFIER:
                self.error_handler.flag(token, 'MISSING_SEMICOLLON', self)
            elif token.value != terminator:
                self.error_handler.flag(token, 'UNEXPECTED_TOKEN', self)
                token = self.next_token()

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
            token = self.next_token()

            op_node.add_child(root_node)

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


def set_line_number(node, token):
    if node:
        node.set_attribute('LINE', token.line_num)
