# -*- coding: utf-8 -*-
import sys

from limbus_core.message import Message, MessageType ,MessageListener
from limbus_core.frontend.token import Token, TokenType, ErrorToken
from limbus_core.frontend.scanner import Scanner
from limbus_core.frontend.source import Source
from limbus_core.backend.backend_factory import BackendFactory
from limbus_core.intermidiate.cross_referencer import CrossReferencer
from limbus_core.intermidiate.parse_tree_printer import ParseTreePrinter

from pascal.pascal_parser import PascalParserTD
from pascal.pascal_error import PascalErrorType, PascalError
from pascal.pascal_token import *


class SourceMessageListener(MessageListener):
    def message_received(self, msg):
        type = msg.type
        body = msg.body
        if type == MessageType.PARSER_SUMMARY:
            print("%d source lines\n%d syntax errors" % (body[0], body[1]))


class ParserMessageListener(MessageListener):
    LINE_FORMAT = ">>> AT LINE %03d\n"
    ASSIGN_FORMAT = ">>> AT LINE %03d: %s = %s\n"
    FETCH_FORMAT = ">>> AT LINE %03d: %s : %s\n"
    CALL_FORMAT = ">>> AT LINE %03d: CALL %s\n"
    RETURN_FORMAT = ">>> AT LINE %03d: RETURN FROM %s\n"

    def message_received(self, msg):
        mtype = msg.type
        body = msg.body

        if mtype == MessageType.TOKEN:
            if body.type == TokenType.ERROR:
                prefix_width = 7
                token = body[0]
                error_message = body[1]
                line = body[2]

                try:
                    space_cnt = prefix_width + token.pos
                except AttributeError:
                    space_cnt = prefix_width

                print("ERROR:", line)
                print(' ' * space_cnt + '^')
                print("*** ", error_message)
                if not token.text:
                    print("at [%s]" % token.text)
            else:
                vs = ""
                if body.type == TokenType.PASCAL:
                    vs = vs + str(body.ptype) + " "

                if body.value:
                    vs = vs + "value = %s" % str(body.value)
                print("%-5s line = %d, pos =%d, text = %s %s" %
                      (body.type, body.line_num, body.pos, body.text, vs))

        elif mtype == MessageType.SYNTAX_ERROR:
            prefix_width = 7
            token = body[0]
            error_message = body[1]
            line = body[2]

            try:
                space_cnt = prefix_width + token.pos
            except AttributeError:
                print("Internal error token = ", token)
                return

            print("ERROR:", line)
            print(' ' * space_cnt + '^')
            print("*** ", error_message)
            if not token.text:
                print("at [%s]" % token.text)


class BackendMessageListener(MessageListener):
    def __init__(self, opts: dict):
        self.lines = opts['lines']
        self.assign = opts['assign']
        self.fetch = opts['fetch']
        self.call = opts['call']
        self.returnn = opts['returnn']
        self.first_output_msg = True


    def message_received(self, msg):
        mtype = msg.type
        body = msg.body
        if mtype == MessageType.INTERPRETER_SUMMARY:
            print('%d statements executed. %d runtime errors.' % (body[0], body[1]))
        elif mtype == MessageType.COMPILER_SUMMARY:
            print('%d instructions generated' % body)
        elif mtype == 'ASSIGN':
            if self.assign:
                line_number, name, value = body
                print(self.ASSIGN_FORMAT % (line_number, name, str(value)))
        elif mtype == 'RUNTIME_ERROR':
            err_msg, line_number = body
            print("*** RUNTIME ERROR")
            if line_number:
                print(' AT LINE %03d' % line_number, end='')
            print(" : ", err_msg)
        elif mtype == 'SOURCE_LINE':
            if self.lines:
                line_number = body
                print(self.LINE_FORMAT % line_number)
        elif mtype == 'FETCH':
            if self.fetch:
                line_number, name, value = body
                print(self.FETCH_FORMAT % (line_number, name, str(value)))
        elif mtype == 'CALL':
            if self.call:
                line_number, routine_name = body
                print(self.CALL_FORMAT % (line_number, routine_name))
        elif mtype == 'RETURN':
            if self.returnn:
                line_number, routine_name = body
                print(self.RETURN_FORMAT % (line_number, routine_name))


class PascalScanner(Scanner):
    special_chars = "<>=()[]{}^.+-*/:.,;'="

    def __init__(self, source):
        super().__init__(source)

    def extract_token(self):
        self.skip_whitespace()
        cc = self.current_char()

        if cc == Scanner.EOF:
            token = Token(self.source)
            token.type = TokenType.EOF
        elif cc.isalpha():
            token = PascalWordToken(self.source)
        elif cc.isdigit():
            token = PascalNumberToken(self.source)
        elif cc == "'":
            token = PascalStringToken(self.source)
        elif cc in PascalScanner.special_chars:
            token = PascalSpecialToken(self.source)
        else:
            token = ErrorToken("PascalScanner", self.source)
            self.next_char()

        return token

    def skip_whitespace(self):
        cc = self.current_char()
        while cc == ' ' or cc == '{' or cc == '\n' :
            # comment
            if cc == '{':
                cc = self.next_char()
                while cc == Scanner.EOF or cc != '}':
                    cc = self.next_char()
                if cc == '}':
                    cc = self.next_char()
            else:
                cc = self.next_char()

    def is_at_eol(self):
        return self.source.is_at_eol()

    def is_at_eof(self):
        return self.source.is_at_eof()

    def is_skip_to_next_line(self):
        return self.source.is_skip_to_next_line()


class Pascal:
    def __init__(self, op, file, flags):
        # options

        self.intermediate =  'i' in flags
        self.xref = 'x' in flags
        self.lines = 'l' in flags
        self.assign = 'a' in flags
        self.fetch = 'f' in flags
        self.call = 'c' in flags
        self.returnn = 'r' in flags
        self.opts = {
            'xref': self.xref,
            'lines': self.lines,
            'assign': self.assign,
            'fetch': self.fetch,
            'call': self.call,
            'returnn': self.returnn
        }

        self.source = Source(open(file))
        self.source.add_message_listener(SourceMessageListener())

        self.scanner = PascalScanner(self.source)
        self.parser = PascalParserTD(self.scanner)
        self.parser.add_message_listener(ParserMessageListener())

        self.backend = BackendFactory().create_backend(op)
        self.backend.add_message_listener(BackendMessageListener(self.opts))

        self.parser.parse()
        self.source.close()

        if self.parser.get_error_count() != 0:
            print("PARSE ERROR, STOP PROCESSING")
            return

        self.symtab_stack = self.parser.get_symTab()
        program_id = self.symtab_stack.get_program_id()
        self.iCode = program_id.get_attribute('ROUTINE_ICODE')

        if self.xref:
            cross_referencer = CrossReferencer()
            cross_referencer.print(self.symtab_stack)

        if self.intermediate:
            with open('tree.xml', 'w') as fp:
                tree_printer = ParseTreePrinter(fp)
                tree_printer.print(self.symtab_stack)

#        self.backend.process(self.iCode, self.symtab_stack)
