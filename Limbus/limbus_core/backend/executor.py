# -*- coding: utf-8 -*-
import sys

from . backend import Backend

from .. intermidiate .symtabstack_impl import SymTabStackIF, SynTabEntryIF
from .. intermidiate .iCode_if import iCodeIF, iCodeNodeIF
from .. intermidiate .iCode_factory import iCodeNodeFactory
from .. message import Message, MessageType

from . runtime_if import RuntimeErrorCode, RuntimeStackIF
from . memory_if import create_memory_map, create_runtime_stack


class RuntimeErrorHandler:
    MAX_ERRORS = 5
    error_count = 0

    def flag(self, node, error_code: RuntimeErrorCode, backend):

        while (not (node is None)) and node.get_attribute('LINE') is None:
            node = node.get_parent()

        msg = Message(MessageType.RUNTIME_ERROR, (error_code.message, node.get_attribute('LINE')))
        backend.send_message(msg)

        self.error_count += 1
        if self.MAX_ERRORS < self.error_count:
            print('*** ABORTED AFTER TOO MANY RUNTIME ERRORS.')
            sys.exit(-1)


class Executor(Backend):

    execution_count: int = 0
    runtime_stack: RuntimeStackIF = create_runtime_stack()
    error_handler: RuntimeErrorHandler = RuntimeErrorHandler()

    def __init__(self, parent):
        self.symtab_stack: SymTabStackIF = None
        super().__init__()

    def get_error_handler(self):
        return self.error_handler

    def increment_exec_count(self):
        self.execution_count += 1

    def process(self, icode: iCodeIF, symtab_stack: SymTabStackIF):
        self.iCode = icode
        self.symtab_stack = symtab_stack
        program_id: SynTabEntryIF = self.symtab_stack.get_program_id()

        call_node: iCodeNodeIF = iCodeNodeFactory().create('CALL')
        call_node.set_attribute('ID', program_id)

        call_executor = CallDeclaredExecutor(self)
        call_executor.execute(call_node)

        runtime_errors = self.error_handler.error_count
        msg = Message(MessageType.INTERPRETER_SUMMARY, (self.execution_count, runtime_errors))
        self.send_message(msg)


class StatementExecutor(Executor):
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
        elif node_type == 'LOOP':
            loop_exec = LoopExecutor(self)
            return loop_exec.execute(node)
        elif node_type == 'IF':
            if_exec = IfExecutor(self)
            return if_exec.execute(node)
        elif node_type == 'SELECT':
            select_exec = SelectExecutor(self)
            return select_exec.execute(node)
        elif node_type == 'NO_OP':
            return None

        else:
            self.error_handler.flag(node, 'UNIMPLEMENTED_FEATURE', self)
            return None

    def send_sourceline_message(self, node):
        line_number = node.get_attribute('LINE')
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
        value = expression_exec.execute(expression_node)

        variable_id = variable_node.get_attribute('ID')
        variable_id.set_attribute('DATA_VALUE', value)

        #print("ASSIGN ", variable_id.name, " ", value, " ", variable_id)

        self._send_message(node, variable_id.get_name(), value)

        self.increment_exec_count()

        return None

    def _send_message(self, node, name, value):
        line_number = node.get_attribute('LINE')
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
            #print("Exe:entry:", entry.name, " ", entry.attribute, " ", entry)
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
            return oprand1 > oprand2
        elif node_type == 'GE':
            return oprand1 >= oprand2

        return 0


class SelectExecutor(StatementExecutor):
    jump_cache = {}

    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        if node in SelectExecutor.jump_cache:
            jump_table = SelectExecutor.jump_cache[node]
        else:
            jump_table = self.create_jumptable(node)
            SelectExecutor.jump_cache[node] = jump_table

        select_children = node.get_children()
        expr_node = select_children[0]
        expression_exec = ExpressionExecutor(self)
        select_value = expression_exec.execute(expr_node)

        if select_value in jump_table:
            statement_node = jump_table[select_value]
            statement_exec = StatementExecutor(self)
            statement_exec.execute(statement_node)

        self.increment_exec_count()
        return None

    def create_jumptable(self, node):
        jump_table = {}

        select_children = node.get_children()

        for i in range(1, len(select_children)):
            branch_node = select_children[i]
            constants_node = branch_node.get_children()[0]
            statement_node = branch_node.get_children()[1]

            constants_list = constants_node.get_children()
            for cn in constants_list:
                value = cn.get_attribute('VALUE')
                jump_table[value] = statement_node

        return jump_table


class LoopExecutor(StatementExecutor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        exit_loop = False
        expr_node = None
        loop_children = node.get_children()

        expression_exec = ExpressionExecutor(self)
        statement_exec = StatementExecutor(self)

        while not exit_loop:
            self.increment_exec_count()
            for child in loop_children:
                child_type = child.get_type()
                if child_type == 'TEST':
                    if expr_node == None:
                        expr_node = child.get_children()[0]
                    exit_loop = expression_exec.execute(expr_node)
                else:
                    statement_exec.execute(child)

                if exit_loop:
                    break

        return None


class IfExecutor(StatementExecutor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        children = node.get_children()
        expr_node = children[0]
        then_stmt_node = children[1]
        if len(children) > 2:
            else_stmt_node = children[2]
        else:
            else_stmt_node = None

        express_exec  = ExpressionExecutor(self)
        statement_exec = StatementExecutor(self)

        b = express_exec.execute(expr_node)

        if b:
            statement_exec.execute(then_stmt_node)
        elif else_stmt_node:
            statement_exec.execute(else_stmt_node)

        self.increment_exec_count()
        return None


class CallDeclaredExecutor():
    def __init__(self, parent):
        pass