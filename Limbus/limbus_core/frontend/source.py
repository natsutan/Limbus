# -*- coding: utf-8 -*-
from .. message import MessageProducer, MessageHandler


class Source(MessageProducer):
    EOL = '\n'
    EOF = None

    def __init__(self, reader):
        self.line_num = 0
        self.current_pos = -2  # -2が最初の値
        self.reader = reader
        self.line = ""
        self.message_handler = MessageHandler()

    def current_char(self):
        # first line
        if self.current_pos == -2:
            self.read_line()
            return self.next_char()

        # eof?
        if self.line == self.EOF:
            return self.EOF

        if self.current_pos > len(self.line):
            self.read_line()
            return self.next_char()

        return self.line[self.current_pos]

    def read_line(self):
        try:
            self.line = self.reader.readline()
        except StopIteration:
            return self.EOF

        self.current_pos = -1
        self.line_num = self.line_num + 1

    def next_char(self):
        self.current_pos = self.current_pos + 1
        return self.current_char()

    def peek_char(self):
        self.current_char()
        if self.line == self.EOF:
            return self.EOF

        next_pos = self.current_pos + 1
        if next_pos > len(self.line):
            return self.line[next_pos]
        else:
            return self.EOL

    def close(self):
        self.reader.close()

    # delegate
    def add_message_listener(self, listener):
        self.message_handler.add_message_listener(listener)

    def remove_message_listener(self, listener):
        self.message_handler.remove_message_listener(listener)

    def send_message(self, message):
        self.message_handler.send_message(message)
