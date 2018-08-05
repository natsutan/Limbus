# -*- coding: utf-8 -*-

import xml.dom.minidom


class ParseTreePrinter:
    def __init__(self, ps):
        self.INDENT_WIDTH = 4
        self.LINE_WIDTH = 160

        self.ps = ps
        self.length = 0
        self.indentation = ""
        self.line = ""
        self.indent = " " * self.INDENT_WIDTH

    def print(self, symtab_stack):
        self.ps.write('<!--- ===== INTERMEDIATE CODE =====  -->\n')
        program_id = symtab_stack.get_program_id()
        self.print_routine(program_id)
        self.print_line()

    def print_line(self):
        if self.length > 0 :
            self.ps.write(self.line + '\n')
            self.line = ""
            self.length = 0

    def append(self, text):
        text_len = len(text)
        line_break = False

        if self.length + text_len > self.LINE_WIDTH:
            self.print_line()
            self.line = self.line + self.indentation
            self.length = len(self.indentation)
            line_break = True

        if not (line_break and text == " "):
            self.line = self.line + text
            self.length = self.length + text_len

    def print_node(self, node):
        self.append(self.indentation)
        self.append("<" + str(node))
        self.print_attributes(node)
        self.print_typespec(node)

        child_node = node.get_children()
        if child_node  and len(child_node) != 0:
            self.append(">")
            self.print_line()
            self.print_child_nodes(child_node)
            self.append(self.indentation)
            self.append("</" + str(node) + ">\n")
        else:
            self.append(" ")
            self.append(">")
            self.print_line()

    def print_attributes(self,  node):
        save_indentation = self.indentation
        self.indentation = self.indentation + self.indent

        for k, v in node.get_all_attributes().items():
            self.print_attribute(k, v)

        self.indentation = save_indentation

    def print_attribute(self, key, value):
        # value がsymtabなら処理を入れる
        is_symtab = value.__class__.__name__ == 'SymTabEntry'

        if is_symtab:
            vs = value.get_name()
        else:
            vs = str(value)

        text = key.lower() + '="' + vs + '"'
        self.append(" ")
        self.append(text)
        if is_symtab:
            level = value.get_symtab().get_nesting_level()
            self.print_attribute("LEVEL", level)

            # ここのコメントを外すとオブジェクトのアドレスが表示される
            #self.append(" ")
            #self.append(str(value))

    def print_child_nodes(self, child_nodes):
        save_indentation = self.indentation
        self.indentation = self.indentation + self.indent

        for cn in child_nodes:
            self.print_node(cn)

        self.indentation = save_indentation

    def print_typespec(self, node):
        typespec = node.get_typespec()

        if typespec:
            save_margin = self.indentation
            self.indentation += self.indent

            type_id = typespec.get_identifier()
            if type_id:
                type_name = type_id.get_name()
            else:
                code = hash(typespec) + hash(typespec.get_form())
                type_name = "$anon_" + str(code)

            self.print_attribute("TYPE_ID", type_name)
            self.indentation = save_margin

    def print_routine(self, routine_id):
        definition = routine_id.get_definition()

        self.append('<!--- *** ' + str(definition) + ' ' + routine_id.get_name() + ' *** -->')
        self.print_line()

        icode = routine_id.get_attribute('ROUTINE_ICODE')
        if icode.get_root():
            self.print_node(icode.get_root())

        rids = routine_id.get_attribute('ROUTINE_ROUTINES')
        for rid in rids:
            self.print_routine(rid)

