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
            return assignment_exec(node)
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

