from limbus_core.frontend.scanner import Scanner
from pascal.pascal_token import *


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
