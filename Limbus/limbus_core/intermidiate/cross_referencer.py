# -*- coding: utf-8 -*-


class CrossReferencer:
    def __init__(self):
        self.NAME_WIDTH = 16
        self.NAME_FORMAT = "%-" + str(self.NAME_WIDTH) + "s"
        self.NUMBERS_LABEL = " Line numbers   "
        self.NUMBERS_UNDERLINE = " ----------- "
        self.NUMBER_FORMAT = "%03d "
        self.LABEL_WIDTH = len(self.NUMBERS_LABEL)
        self.INDENT_WIDTH = self.NAME_WIDTH + self.LABEL_WIDTH
        self.INDENT = " " * self.INDENT_WIDTH

    def print(self, symtab_stack):
        print("====== CROSS-REFERENCE TABLE ======")
        self.print_column_headings()
        self.print_symtab(symtab_stack.get_local_symtab())

    def print_column_headings(self):
        print()
        print(self.NAME_FORMAT % "Identifier", self.NUMBERS_LABEL)
        print(self.NAME_FORMAT % "----------", self.NUMBERS_UNDERLINE)

    def print_symtab(self, symtab):
        sorted = symtab.get_sorted_entries()
        for entry in sorted:
            line_numbers = entry.get_line_numbers()
            print(self.NAME_FORMAT % entry.get_name(), end='')
            for l in line_numbers:
                print(self.NUMBER_FORMAT % l, end='')
            print()
