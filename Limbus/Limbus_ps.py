# -*- coding: utf-8 -*-
from limbus_core.message import Message, MessageType
from limbus_core.frontend.parser import Parser
from limbus_core.frontend.token import Token
from limbus_core.frontend.scanner import Scanner


class PascalParserTD(Parser):
    def __init__(self, scanner):
        super(Parser, self).__init__(scanner)

    def parse(self):
        token = self.next_token()
        while token.type != Token.EOF:
            token = self.next_token()

        line_number = self.get_line_number()
        err_cnt = self.get_error_count()

        msg = Message(MessageType.PARSER_SUMMARY, (line_number, err_cnt))
        self.send_message(msg)

    def get_error_count(self):
        return 0


class PascalScanner(Scanner):
    def __init__(self, source):
        super(Scanner, self).__init__(source)

    def extra_token(self):
        cc = self.current_char()
        if cc == Scanner.EOF:
            token = Token(self.source)
            token.type = Token.EOF
        else:
            token = Token(self.source)
        return token


def main():
    pass


if __name__ == '__main__':
    main()




