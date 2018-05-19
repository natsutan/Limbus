# -*- coding: utf-8 -*-
from limbus_core.message import Message, MessageType ,MessageListener
from limbus_core.frontend.parser import Parser
from limbus_core.frontend.token import Token, TokenType
from limbus_core.frontend.scanner import Scanner
from limbus_core.frontend.source import Source
from limbus_core.backend.backend_factory import BackendFactory


class SourceMessageListener(MessageListener):
    def message_received(self, msg):
        type = msg.type
        body = msg.body
        if type == MessageType.PARSER_SUMMARY:
            print("%d source lines%s\n%d syntax errors" % (body[0], body[1]))


class ParserMessageListener(MessageListener):
    def message_received(self, msg):
        type = msg.type
        body = msg.body
        if type == MessageType.SOURCE_LINE:
            print("%3d %s" % (body[0], body[1]))


class BackendMessageListener(MessageListener):
    def message_received(self, msg):
        type = msg.type
        body = msg.body
        if type == MessageType.INTERPRETER_SUMMARY:
            print('%d statements executed. %d runtime errors.' % (body[0], body[1]))
        elif type == MessageType.COMPILER_SUMMARY:
            print('%d instructions generated' % body)


class PascalParserTD(Parser):
    def __init__(self, scanner):
        super().__init__(scanner)

    def parse(self):
        token = self.next_token()
        while token.type != TokenType.EOF:
            token = self.next_token()

        line_number = self.get_line_number()
        err_cnt = self.get_error_count()

        msg = Message(MessageType.PARSER_SUMMARY, (line_number, err_cnt))
        self.send_message(msg)

    def get_error_count(self):
        return 0


class PascalScanner(Scanner):
    def __init__(self, source):
        super().__init__(source)

    def extract_token(self):
        cc = self.current_char()
        if cc == Scanner.EOF:
            token = Token(self.source)
            token.type = Token.EOF
        else:
            token = Token(self.source)
        return token


class Pascal:
    def __init__(self, op, file, flags):
        # options
        if 'i' in flags:
            self.intermediate = flags['i'] > - 1
        else:
            self.intermediate = False

        if 'x' in flags:
            self.xref = flags['x'] > -1
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
        self.symTab = self.parser.get_symTab()

        self.backend.process(self.iCode, self.symTab)

