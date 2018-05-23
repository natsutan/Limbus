# -*- coding: utf-8 -*-
import sys

from limbus_core.message import Message, MessageType ,MessageListener
from limbus_core.frontend.parser import Parser
from limbus_core.frontend.token import Token, TokenType, ErrorToken
from limbus_core.frontend.scanner import Scanner
from limbus_core.frontend.source import Source
from limbus_core.backend.backend_factory import BackendFactory

from pascal_error import PascalErrorType, PascalError
from pascal_token import *


class SourceMessageListener(MessageListener):
    def message_received(self, msg):
        type = msg.type
        body = msg.body
        if type == MessageType.PARSER_SUMMARY:
            print("%d source lines\n%d syntax errors" % (body[0], body[1]))


class ParserMessageListener(MessageListener):
    def message_received(self, msg):
        mtype = msg.type
        body = msg.body

        if mtype == MessageType.TOKEN:
            if body.type == TokenType.ERROR:
                prefix_width = 7
                token = body[0]
                error_message = body[1]
                line = body[2]

                space_cnt = prefix_width + token.pos

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

            space_cnt = prefix_width + token.pos

            print("ERROR:", line)
            print(' ' * space_cnt + '^')
            print("*** ", error_message)
            if not token.text:
                print("at [%s]" % token.text)


class BackendMessageListener(MessageListener):
    def message_received(self, msg):
        mtype = msg.type
        body = msg.body
        if mtype == MessageType.INTERPRETER_SUMMARY:
            print('%d statements executed. %d runtime errors.' % (body[0], body[1]))
        elif mtype == MessageType.COMPILER_SUMMARY:
            print('%d instructions generated' % body)


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


class PascalParserTD(Parser):
    def __init__(self, scanner):
        self.error_handler = PascalErrorHandler()
        super().__init__(scanner)

    def parse(self):
        token = self.next_token()
        while token.type != TokenType.EOF:
            if token.type != TokenType.ERROR:
                msg = Message(MessageType.TOKEN, token)
                self.send_message(msg)
            else:
                self.error_handler.flag(token, token.error_code, self)

            token = self.next_token()

        line_number = token.line_num
        err_cnt = self.get_error_count()

        msg = Message(MessageType.PARSER_SUMMARY, (line_number, err_cnt))
        self.send_message(msg)

    def get_error_count(self):
        return self.error_handler.get_error_count()

    def get_iCode(self):
        return []

    def get_symTab(self):
        return []

    def get_line(self):
        return self.scanner.source.line


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


class Pascal:
    def __init__(self, op, file, flags):
        # options
        if 'i' in flags:
            self.intermediate = True
        else:
            self.intermediate = False

        if 'x' in flags:
            self.xref = True
        else:
            self.xref = False

        self.source = Source(open(file))
        self.source.add_message_listener(SourceMessageListener())

        self.scanner = PascalScanner(self.source)
        self.parser = PascalParserTD(self.scanner)
        self.parser.add_message_listener(ParserMessageListener())

        self.backend = BackendFactory().create_backend(op)
        self.backend.add_message_listener(BackendMessageListener())

        self.parser.parse()
        self.source.close()

        self.iCode = self.parser.get_iCode()
        self.symtab_stack = self.parser.get_symTab()

        if self.xref :
            cross_referencer = CrossReferencer()
            cross_referencer.print(symtabb_stack)

        self.backend.process(self.iCode, self.symtab_stack)

