# -*- coding: utf-8 -*-
import sys

from limbus_core.message import Message, MessageType ,MessageListener

class RunTimeErrorHandler:

    def __init__(self):
        self.MAX_ERRORS = 5
        self.error_count = 0

    def get_error_count(self):
        return self.error_count

    def flag(self, node, error_code, backend):
        line_number = ""
        while node and node.get_attribute("LINE"):
            node = node.get_parent()

        msg = Message(error_code, node.get_attribute('LINE'))
        backend.send_message('RUNTIME_ERROR', msg)

        self.error_count += 1
        if self.error_count > self.MAX_ERRORS:
            print("*** ABORTED AFTER TOO MANY RUNTIME ERRORS.")
            sys.exit(1)
