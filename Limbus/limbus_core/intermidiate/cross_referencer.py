# -*- coding: utf-8 -*-

from limbus_core.intermidiate.type_impl import Predefined, Definition, TypeSpec, TypeForm
from limbus_core.intermidiate.symtabstack_impl import SymTabKey

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
        self.ENUM_CONST_FORMAT = "%" + str(self.NAME_WIDTH) + "s = %s"


    def print(self, symtab_stack):
        print("====== CROSS-REFERENCE TABLE ======")
        program_id = symtab_stack.get_program_id()
        self.print_routine(program_id)

    def print_routine(self, routine_id):
        definiton = routine_id.get_definition()
        print("\n***" + str(definiton) + " " + routine_id.get_name() + " ***")
        self.print_column_headings()
        symtab = routine_id.get_attribute(SymTabKey.ROUTINE_SYMTAB)
        new_record_types = []
        self.print_symtab(symtab, new_record_types)
        if len(new_record_types) > 0:
            self.print_records(new_record_types)

        routine_ids = routine_id.get_attribute(SymTabKey.ROUTINE_ROUTINES)
        if routine_ids:
            for rid in routine_ids:
                self.print_routine(rid)

    def print_records(self, record_types):
        for record_type in record_types:
            record_id = record_type.get_identifier()
            if record_id:
                name = record_id.get_name()
            else:
                name = "<unnamed>"

            print("\n--- RECORD " + name + " ---")
            self.print_column_headings()

            symtab = record_type.get_attribute('RECORD_SYMTAB')
            new_recoerd_types = []
            self.print_symtab(symtab, new_recoerd_types)

            if len(new_recoerd_types) > 0:
                self.print_records(new_recoerd_types)


    def print_column_headings(self):
        print()
        print(self.NAME_FORMAT % "Identifier", self.NUMBERS_LABEL)
        print(self.NAME_FORMAT % "----------", self.NUMBERS_UNDERLINE)

    def print_symtab(self, symtab, record_types):
        sorted = symtab.get_sorted_entries()
        for entry in sorted:
            line_numbers = entry.get_line_numbers()
            print(self.NAME_FORMAT % entry.get_name(), end='')
            for l in line_numbers:
                print(self.NUMBER_FORMAT % l, end='')
            print()

            self.print_entry(entry, record_types)

    def print_entry(self, entry, record_types):
        definition = entry.get_definition()
        nesting_level = entry.get_symtab().get_nesting_level()
        print(self.INDENT + "Defined as: " + definition.get_text())
        print(self.INDENT + "scope nesting level: " + str(nesting_level))

        type = entry.get_typespec()
        self.print_type(type)

        if definition == Definition.CONSTANT:
            val = entry.get_attribute('CONSTANT_VALUE')
            print(self.INDENT + "Value = " + str(val))

            if type.get_identifier():
                self.print_type_detail(type, record_types)
        elif definition == Definition.ENUMERATION_CONSTANT:
            val = entry.get_attribute('CONSTANT_VALUE')
            print(self.INDENT + "Value = " + str(val))
        elif definition == Definition.TYPE:
            if entry == type.get_identifier():
                self.print_type_detail(type, record_types)
        elif definition == Definition.VARIABLE:
            # typeの情報がないの時のみ表示する。
            if not type.get_identifier():
                self.print_type_detail(type, record_types)


    def print_type(self, type):
        if type:
            form = type.get_form()
            typeid = type.get_identifier()
            if typeid:
                type_name = type.get_name()
            else:
                type_name = "<unnamed>"
            print(self.INDENT + "Type form = " + form + ", type id = " + type_name)


    def print_type_detail(self, type, record_type):
        form = type.get_form()
        
        if form == TypeForm.ENUMERATION:
            constant_ids = type.get_attribute('ENUMERATION_CONSTANTS')
            print(self.INDENT + "--- Enumeration constants ---")

            for const_id in constant_ids:
                name = const_id.get_name()
                value = const_id.get_attribute('CONSTANT_VALUE')
                print(self.INDENT + (self.ENUM_CONST_FORMAT % (name, str(value))))
        elif form == TypeForm.SUBRANGE:
            min_val = type.get_attribute('SUBRANGE_MIN_VALUE')
            max_val = type.get_attribute('SUBRANGE_MAX_VALUE')
            base_type_spec = type.get_attribute('SUBRANGE_BASE_TYPE')

            print(self.INDENT + '---BASE TYPE ---')
            self.print_type(base_type_spec)

            # 名前がない時のみ表示
            if not base_type_spec.get_identifier():
                self.print_type_detail(base_type_spec, record_type)
            print(self.INDENT + "Range = " + str(min_val) + '..' + str(max_val))
        elif form == TypeForm.ARRAY:
            index_type = type.get_attribute('ARRAY_INDEX_TYPE')
            element_type = type.get_attribute('ARRAY_ELEMENT_TYPE')
            count = type.get_attribute('ARRAY_ELEMENT_COUNT')

            print(self.INDENT + "--- INDEX TYPE ---")
            self.print_type(index_type)
            if not index_type.get_identifier():
                self.print_type_detail(type, record_type)

            print(self.INDENT + "--- ELEMENT TYPE ---")
            self.print_type(element_type)
            print(self.INDENT + str(count) + " elements")
            if not element_type.get_identifier():
                self.print_type_detail(element_type, record_type)
        elif form == TypeForm.RECORD:
            record_type.append(type)



