# -*- coding: utf-8 -*-
from . backend import Backend
from .. message import Message, MessageType


class RunTimeErrorHandler:
    def __init__(self):
        self.MAX_ERRORS = 5
        self.error_count = 0

    def get_error_count(self):
        return self.error_count

    def flag(self, node, error_code, backend):
        # line_number = ""
        while node and node.get_attribute("LINE"):
            node = node.get_parent()

        msg = Message(error_code, node.get_attribute('LINE'))
        backend.send_message('RUNTIME_ERROR', msg)

        self.error_count += 1
        if self.error_count > self.MAX_ERRORS:
            print("*** ABORTED AFTER TOO MANY RUNTIME ERRORS.")
            sys.exit(1)


class Executer(Backend):
    error_handler = RunTimeErrorHandler()
    execution_count = 0
    runtime_error = 0

    def __init__(self):
        super().__init__()

    def get_error_handler(self):
        return Executer.error_handler

    def increment_exec_count(self):
        Executer.execution_count += 1

    def process(self, icode, symtab):
        self.iCode = icode
        self.symtab = symtab

        root_node = self.iCode.get_root()
        statement_exec = StatementExecutor(self)
        statement_exec.execute(root_node)

        ec = 0
        re = 0
        msg = Message(MessageType.EXECUTE_SUMMARY, (ec, re))
        self.send_message(msg)


class StatementExecutor(Executer):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        node_type = node.type
        self.send_sourceline_message(node)

        if node_type == 'COMPOUND':
            coupound_exec = CompoundExecutor(self)
            return coupound_exec.execute(node)
        elif node_type == 'ASSIGN':
            assignment_exec = AssignmentExecutor(self)
            return assignment_exec.execute(node)
        elif node_type == 'NO_OP':
            return None

        else:
            self.error_handler.flag(node, 'UNIMPLEMENTED_FEATURE', self)
            return None

    def send_sourceline_message(self, node):
        line_number = node.get_attrbute('LINE')
        if line_number:
            msg =  Message(MessageType.SOURCE_LINE, line_number)
            self.message_handler.send_message(msg)


class CompoundExecutor(StatementExecutor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        statement_exec = StatementExecutor(self)
        for c in node.get_children():
            statement_exec.execute(c)

        return None


class AssignmentExecutor(StatementExecutor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        children = node.get_children()
        variable_node = children[0]
        expression_node = children[1]

        expression_exec = ExpressionExecutor(self)
        value = expression_exec.execution(expression_node)

        variable_id = variable_node.get_attribute('ID')
        variable_id.set_attribute('DATA_VALUE', value)

        self._send_message(node, variable_id.get_name(), value)

        self.increment_exec_count()

        return None

    def _send_message(self, node, name, value):
        line_number = node.get_attrbute('LINE')
        if line_number:
            msg = Message('ASSIGN', (line_number, name, value))
            self.send_message(msg)

class ExpressionExecutor(StatementExecutor):

    def __init__(self, parent):
        self.ARITH_OPS = ['ADD', 'SUBTRACT', 'MULTIPLY', 'FLOAT_DIVIDE', 'INTEGER_DIVIDE', 'MOD']
        super().__init__(parent)

    def execute(self, node):
        node_type = node.type

        if node_type == 'VARIABLE':
            entry = node.get_attribute('ID')
            val = entry.get_attribute('DATA_VALUE')
            return val
        elif node_type == 'INTEGER_CONSTANT':
            val = int(node.get_attribute('VALUE'))
            return val
        elif node_type == 'REAL_CONSTANT':
            val = float(node.get_attribute('VALUE'))
            return val
        elif node_type == 'STRING_CONSTANT':
            val = str(node.get_attribute('VALUE'))
            return val
        elif node_type == 'NEGATE':
            children = node.get_children()
            expression_node = children[0]
            value = self.execute(expression_node)
            return - value
        elif node_type == 'NOT':
            children = node.get_children()
            expression_node = children[0]
            value = self.execute(expression_node)
            return not value
        else:
            value = self.execute_binary_op(node, node_type)
            return value

    def execute_binary_op(self, node, node_type):
        children = node.get_children()
        opnode1 = children[0]
        opnode2 = children[1]

        oprand1 = self.execute(opnode1)
        oprand2 = self.execute(opnode2)

        intmode = isinstance(oprand1, int) and isinstance(oprand2, int)

        if node_type in self.ARITH_OPS:
            if intmode:
                value1 = int(oprand1)
                value2 = int(oprand2)
                if node_type == 'ADD':
                    return value1 + value2
                elif node_type == 'SUBTRACT':
                    return  value1 - value2
                elif node_type == 'MULTIPLY':
                    return value1 * value2
                elif node_type == 'FLOAT_DIVIDE':
                    if value2 != 0:
                        return float(value1) / float(value2)
                    else:
                        self.error_handler.flag(node, 'DIVISION_BY_ZERO', self)
                        return 0
                elif node_type == 'INTEGER_DIVIDE':
                    if value2 != 0:
                        return int(value1/value2)
                    else:
                        self.error_handler.flag(node, 'DIVISION_BY_ZERO', self)
                        return 0
                elif node_type == 'MOD':
                    if value2 != 0:
                        return  value1 % value2
                    else:
                        self.error_handler.flag(node, 'DIVISION_BY_ZERO', self)
                        return 0
            else:
                # float mode
                value1 = float(oprand1)
                value2 = float(oprand2)
                if node_type == 'ADD':
                    return value1 + value2
                elif node_type == 'SUBTRACT':
                    return  value1 - value2
                elif node_type == 'MULTIPLY':
                    return value1 * value2
                elif node_type == 'FLOAT_DIVIDE':
                    if value2 != 0:
                        return value1 / value2
                    else:
                        self.error_handler.flag(node, 'DIVISION_BY_ZERO', self)
                        return 0
        elif node_type == 'AND':
            return oprand1 and oprand2
        elif node_type == 'OR':
            return oprand1 or oprand2
        if node_type == 'EQ':
            return oprand1 == oprand2
        elif node_type == 'NE':
            return oprand1 != oprand2
        elif node_type == 'LT':
            return oprand1 <  oprand2
        elif node_type == 'LE':
            return oprand1 <= oprand2
        elif node_type == 'GT':
            return oprand1 >  oprand2
        elif node_type == 'GE':
            return oprand1 >= oprand2

        return 0




