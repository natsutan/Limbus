# -*- coding: utf-8 -*-
from limbus_core.intermidiate.type_impl import Predefined, Definition, TypeForm

class TypeChecker:
    def is_integer(self, type):
        if type:
            return type.base_type() == Predefined.integer_type
        else:
            return False

    def are_both_integer(self, type1, type2):
        return self.is_integer(type1) and self.is_integer(type2)


    def is_real(self, type):
        if type:
            return type.base_type() == Predefined.real_type
        else:
            return False

    def is_at_least_one_real(self, type1, type2):
        t1_int = self.is_integer(type1)
        t2_int = self.is_integer(type2)
        t1_real = self.is_real(type1)
        t2_real = self.is_real(type2)

        return (t1_real and t2_real) or (t1_real and t2_int) or (t1_int and t2_real)

    def is_bool(self, type):
        if type:
            return type.base_type() == Predefined.boolean_type
        else:
            return False

    def are_both_boolean(self, type1, type2):
        return self.is_bool(type1) and self.is_bool(type2)

    def is_char(self, type):
        if type:
            return type.base_type() == Predefined.char_type
        else:
            return False

    def are_assignment_compatible(self, target_type, value_type):
        if target_type == None or value_type == None:
            return False

        ttype = target_type.base_type()
        vtyep = value_type.base_type()

        if ttype == vtyep:
            compatible = True
        elif self.is_real(target_type) and self.is_integer(value_type):
            compatible = True
        else:
            compatible = target_type.is_pascal_string() and value_type.is_pascal_string()

        return compatible

    def are_comparison_compatible(self, type1, type2):
        if type1 == None and type2 == None:
            return False

        t1 = type1.base_type()
        t2 = type2.base_type()
        form = t1.get_form()

        if (t1 == t2) and ((form == TypeForm.SCALAR) or (form == TypeForm.ENUMERATION)):
            compatible = True
        elif self.is_at_least_one_real(type1, type2):
            compatible = True
        else:
            compatible = target_type.is_pascal_string() and value_type.is_pascal_string()

        return compatible





