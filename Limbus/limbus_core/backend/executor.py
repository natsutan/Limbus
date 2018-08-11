# -*- coding: utf-8 -*-
import sys
import copy
import math

from . backend import Backend
from .backend_factory import object_default_value

from ... pascal.pascal_limbus import PascalScanner
from .. frontend.source import Source
from .. intermidiate .symtabstack_impl import SymTabStackIF, SynTabEntryIF
from .. intermidiate .iCode_if import iCodeIF, iCodeNodeIF, iCodeNodeType
from .. intermidiate .iCode_factory import iCodeNodeFactory
from .. intermidiate. type_impl import TypeSpec, Predefined, Definition, TypeForm
from .. message import Message, MessageType

from . runtime_if import RuntimeErrorCode, RuntimeStackIF, CellIF
from . memory_if import create_runtime_stack, create_active_recode
from . activation_record_if import ActivationRecordIF


class RuntimeErrorHandler:
    MAX_ERRORS = 5
    error_count = 0

    def flag(self, node, error_code: RuntimeErrorCode, backend: Backend):

        while node is not None and node.get_attribute('LINE') is None:
            node = node.get_parent()

        msg = Message(MessageType.RUNTIME_ERROR, (error_code.message, node.get_attribute('LINE')))
        backend.send_message(msg)

        self.error_count += 1
        if self.MAX_ERRORS < self.error_count:
            print('*** ABORTED AFTER TOO MANY RUNTIME ERRORS.')
            sys.exit(-1)


class Executor(Backend):

    execution_count: int = 0
    runtime_stack: RuntimeStackIF = create_runtime_stack()
    error_handler: RuntimeErrorHandler = RuntimeErrorHandler()

    standard_in = PascalScanner(sys.__stdin__)
    standard_out = sys.__stdout__

    def __init__(self, parent):
        self.symtab_stack: SymTabStackIF = None
        super().__init__()

    def get_error_handler(self):
        return self.error_handler

    def increment_exec_count(self):
        self.execution_count += 1

    def process(self, icode: iCodeIF, symtab_stack: SymTabStackIF):
        self.iCode = icode
        self.symtab_stack = symtab_stack
        program_id: SynTabEntryIF = self.symtab_stack.get_program_id()

        call_node: iCodeNodeIF = iCodeNodeFactory().create('CALL')
        call_node.set_attribute('ID', program_id)

        call_executor = CallDeclaredExecutor(self)
        call_executor.execute(call_node)

        runtime_errors = self.error_handler.error_count
        msg = Message(MessageType.INTERPRETER_SUMMARY, (self.execution_count, runtime_errors))
        self.send_message(msg)


class StatementExecutor(Executor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node: iCodeNodeIF):
        node_type = node.get_type()
        self.send_sourceline_message(node)

        if node_type == 'COMPOUND':
            coupound_exec = CompoundExecutor(self)
            return coupound_exec.execute(node)
        elif node_type == 'ASSIGN':
            assignment_exec = AssignmentExecutor(self)
            return assignment_exec.execute(node)
        elif node_type == 'LOOP':
            loop_exec = LoopExecutor(self)
            return loop_exec.execute(node)
        elif node_type == 'IF':
            if_exec = IfExecutor(self)
            return if_exec.execute(node)
        elif node_type == 'SELECT':
            select_exec = SelectExecutor(self)
            return select_exec.execute(node)
        elif node_type == 'NO_OP':
            return None

        else:
            self.error_handler.flag(node, 'UNIMPLEMENTED_FEATURE', self)
            return None

    def send_sourceline_message(self, node):
        line_number = node.get_attribute('LINE')
        if line_number:
            msg =  Message(MessageType.SOURCE_LINE, line_number)
            self.message_handler.send_message(msg)

    # TODO
    def check_range(self, node: iCodeNodeIF, typespec: TypeSpec, value):
        return value

    def copy_of(self, value, node: iCodeNodeIF):
        return value

    def send_assign_message(self, node: iCodeNodeIF, variable_name:str, value):
        pass

    def send_call_message(self, note: iCodeNodeIF, routine_name: str):
        pass

    def send_return_message(self, node: iCodeNodeIF, routine_name: str):
        pass

    def send_fetch_message(self, node: iCodeNodeIF, variable_name: str, value):
        pass

    def get_line_number(self, node: iCodeNodeIF):
        return None

    def to_java(self, target_type: TypeSpec, pascal_value):
        pass

class CompoundExecutor(StatementExecutor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        statement_exec = StatementExecutor(self)
        for c in node.get_children():
            statement_exec.execute(c)

        return None


class AssignmentExecutor(StatementExecutor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node: iCodeNodeIF):
        children: list = node.get_children()
        variable_node: iCodeNodeIF = children[0]
        expression_node: iCodeNodeIF = children[1]
        variable_id: SynTabEntryIF = variable_node.get_attribute('ID')

        expression_exec = ExpressionExecutor(self)
        value = expression_exec.execute(expression_node)
        target_cell: CellIF = expression_exec.execute_variable(variable_node)

        target_type: TypeSpec = variable_node.get_typespec()
        value_type: TypeSpec = expression_node.get_typespec().base_type()
        value = expression_exec.execute(expression_node)

        self.assign_value(node, variable_id, target_cell, target_type, value, value_type)
        self.increment_exec_count()

        return None

    def assign_value(self, node: iCodeNodeIF, target_id: SynTabEntryIF, target_cell: CellIF, target_type: TypeSpec,
                     value, value_type: TypeSpec):
        value = self.check_range(node, target_type, value)

        # Convert an integer value to real if necessary.
        if target_type == Predefined.real_type and value_type == Predefined.integer_type:
            target_cell.value = float(value)
        elif target_type.is_pascal_string():
            target_length: int = target_type.get_attribute('ARRAY_ELEMENT_COUNT')
            value_length: int = value_type.get_attribute('ARRAY_ELEMENT_COUNT')
            string_value: str = str(value)

            if target_length > value_length:
                string_value += ' ' * (target_length - value_length)

            target_cell.value = self.copy_of(string_value, node)
        else:
            target_cell.value= self.copy_of(value, node)

        self.send_assign_message(node, target_id.get_name(), value)

    def _send_message(self, node, name, value):
        line_number = node.get_attribute('LINE')
        if line_number:
            msg = Message('ASSIGN', (line_number, name, value))
            self.send_message(msg)


class ExpressionExecutor(StatementExecutor):

    def __init__(self, parent):
        self.ARITH_OPS = ['ADD', 'SUBTRACT', 'MULTIPLY', 'FLOAT_DIVIDE', 'INTEGER_DIVIDE', 'MOD']
        super().__init__(parent)

    def execute(self, node):
        node_type = node.type

        if node_type == 'VARIABLE':
            entry = node.get_attribute('ID')
            val = entry.get_attribute('DATA_VALUE')
            return val
        elif node_type == 'INTEGER_CONSTANT':
            val = int(node.get_attribute('VALUE'))
            return val
        elif node_type == 'REAL_CONSTANT':
            val = float(node.get_attribute('VALUE'))
            return val
        elif node_type == 'STRING_CONSTANT':
            val = str(node.get_attribute('VALUE'))
            return val
        elif node_type == 'NEGATE':
            children = node.get_children()
            expression_node = children[0]
            value = self.execute(expression_node)
            return - value
        elif node_type == 'NOT':
            children = node.get_children()
            expression_node = children[0]
            value = self.execute(expression_node)
            return not value
        elif node_type == 'CALL':
            function_id: SynTabEntryIF = node.get_attribute('ID')
            routine_code: str = function_id.get_attribute('ROUTINE_CODE')
            call_exec = CallExecutor(self)
            value = call_exec.execute(node)

            if routine_code == 'DECLARED':
                function_name: str = function_id.get_name()
                nesting_level: int = function_id.get_symtab().get_nesting_level()
                ar: ActivationRecordIF = self.runtime_stack.get_topmost(nesting_level)
                function_value_cell: CellIF = ar.get_cell(function_name)
                value = function_value_cell.value
                self.send_fetch_message(node, function_id.get_name(), value)

            return value
        else:
            value = self.execute_binary_op(node, node_type)
            return value

    def execute_value(self, node: iCodeNodeIF):
        variable_id: SynTabEntryIF = node.get_attribute('ID')
        variable_name: str = variable_id.get_name()
        variable_type: TypeSpec = variable_id.get_typespec()

        variable_cell: CellIF = self.execute_variable(node)
        value = variable_cell.value

        if value is not None:
            value = self.to_java(variable_type, value)
        else:
            self.error_handler.flag(node, 'UNINITIALIZED_VALUE', self)
            value = object_default_value(variable_type)
            variable_cell.value = value
        self.send_fetch_message(node, variable_name, value)
        return value

    def execute_binary_op(self, node, node_type):
        children = node.get_children()
        opnode1 = children[0]
        opnode2 = children[1]

        oprand1 = self.execute(opnode1)
        oprand2 = self.execute(opnode2)

        intmode: bool = False
        char_mode: bool = False
        str_mode: bool = False

        if isinstance(oprand1, int) and isinstance(oprand2, int):
            intmode = True
        elif (isinstance(oprand1, str) and len(oprand1) == 1) and (isinstance(oprand2, str) and len(oprand2) == 1):
            char_mode = True
        elif isinstance(oprand1, str) and isinstance(oprand2, str):
            str_mode = True

        if node_type in self.ARITH_OPS:
            if intmode:
                value1 = int(oprand1)
                value2 = int(oprand2)
                if node_type == 'ADD':
                    return value1 + value2
                elif node_type == 'SUBTRACT':
                    return  value1 - value2
                elif node_type == 'MULTIPLY':
                    return value1 * value2
                elif node_type == 'FLOAT_DIVIDE':
                    if value2 != 0:
                        return float(value1) / float(value2)
                    else:
                        self.error_handler.flag(node, 'DIVISION_BY_ZERO', self)
                        return 0
                elif node_type == 'INTEGER_DIVIDE':
                    if value2 != 0:
                        return int(value1/value2)
                    else:
                        self.error_handler.flag(node, 'DIVISION_BY_ZERO', self)
                        return 0
                elif node_type == 'MOD':
                    if value2 != 0:
                        return  value1 % value2
                    else:
                        self.error_handler.flag(node, 'DIVISION_BY_ZERO', self)
                        return 0
            else:
                # float mode
                value1 = float(oprand1)
                value2 = float(oprand2)
                if node_type == 'ADD':
                    return value1 + value2
                elif node_type == 'SUBTRACT':
                    return  value1 - value2
                elif node_type == 'MULTIPLY':
                    return value1 * value2
                elif node_type == 'FLOAT_DIVIDE':
                    if value2 != 0:
                        return value1 / value2
                    else:
                        self.error_handler.flag(node, 'DIVISION_BY_ZERO', self)
                        return 0
        # とりあえずそのままで。
        elif node_type == 'AND':
            return oprand1 and oprand2
        elif node_type == 'OR':
            return oprand1 or oprand2
        if node_type == 'EQ':
            return oprand1 == oprand2
        elif node_type == 'NE':
            return oprand1 != oprand2
        elif node_type == 'LT':
            return oprand1 <  oprand2
        elif node_type == 'LE':
            return oprand1 <= oprand2
        elif node_type == 'GT':
            return oprand1 > oprand2
        elif node_type == 'GE':
            return oprand1 >= oprand2

        return 0

    def execute_variable(self, node: iCodeNodeIF) -> CellIF:
        variable_id: SynTabEntryIF = node.get_attribute('ID')
        variable_name: str = variable_id.get_name()
        variable_type: TypeSpec = variable_id.get_typespec()
        nesting_level: int = variable_id.get_symtab().get_nesting_level()

        ar: ActivationRecordIF = self.runtime_stack.get_topmost(nesting_level)
        variable_cell: CellIF = ar.get_cell(variable_name)

        modifiers: [iCodeNodeIF] = node.get_children()

        if isinstance(variable_cell.value, CellIF):
            variable_cell = variable_cell.value

        for modifier in modifiers:
            node_type: iCodeNodeType = modifier.get_type()

            if node_type == iCodeNodeType.SUBSCRIPTS:
                subscripts: [iCodeNodeIF] = modifier.get_children()
                for subscript in subscripts:
                    index_type: TypeSpec = variable_type.get_attribute('ARRAY_INDEX_TYPE')
                    if index_type.get_form() == TypeForm.SUBRANGE:
                        min_index: int = index_type.get_attribute('SUBRANGE_MIN_VALUE')
                    else:
                        min_index = 0
                    value: int = self.execute(subscript)
                    value: int = self.check_range(node, index_type, value)

                    index: int = value - min_index
                    variable_cell: [CellIF] = variable_cell.value[index]
                    variable_type: TypeSpec = variable_type.get_attribute('ARRAY_ELEMENT_TYPE')

            elif node_type == iCodeNodeType.FIELD:
                field_id: SynTabEntryIF = modifier.get_attribute('ID')
                field_name: str = field_id.get_name()
                field_map: dict = variable_cell.value
                variable_cell = field_map[field_name]
                variable_type = field_id.get_typespec()

        return variable_cell


class SelectExecutor(StatementExecutor):
    jump_cache = {}

    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        if node in SelectExecutor.jump_cache:
            jump_table = SelectExecutor.jump_cache[node]
        else:
            jump_table = self.create_jumptable(node)
            SelectExecutor.jump_cache[node] = jump_table

        select_children = node.get_children()
        expr_node = select_children[0]
        expression_exec = ExpressionExecutor(self)
        select_value = expression_exec.execute(expr_node)

        if select_value in jump_table:
            statement_node = jump_table[select_value]
            statement_exec = StatementExecutor(self)
            statement_exec.execute(statement_node)

        self.increment_exec_count()
        return None

    def create_jumptable(self, node):
        jump_table = {}

        select_children = node.get_children()

        for i in range(1, len(select_children)):
            branch_node = select_children[i]
            constants_node = branch_node.get_children()[0]
            statement_node = branch_node.get_children()[1]

            constants_list = constants_node.get_children()
            for cn in constants_list:
                value = cn.get_attribute('VALUE')
                jump_table[value] = statement_node

        return jump_table


class LoopExecutor(StatementExecutor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        exit_loop = False
        expr_node = None
        loop_children = node.get_children()

        expression_exec = ExpressionExecutor(self)
        statement_exec = StatementExecutor(self)

        while not exit_loop:
            self.increment_exec_count()
            for child in loop_children:
                child_type = child.get_type()
                if child_type == 'TEST':
                    if expr_node is None:
                        expr_node = child.get_children()[0]
                    exit_loop = expression_exec.execute(expr_node)
                else:
                    statement_exec.execute(child)

                if exit_loop:
                    break

        return None


class IfExecutor(StatementExecutor):
    def __init__(self, parent):
        super().__init__(parent)

    def execute(self, node):
        children = node.get_children()
        expr_node = children[0]
        then_stmt_node = children[1]
        if len(children) > 2:
            else_stmt_node = children[2]
        else:
            else_stmt_node = None

        express_exec  = ExpressionExecutor(self)
        statement_exec = StatementExecutor(self)

        b = express_exec.execute(expr_node)

        if b:
            statement_exec.execute(then_stmt_node)
        elif else_stmt_node:
            statement_exec.execute(else_stmt_node)

        self.increment_exec_count()
        return None


class CallExecutor(StatementExecutor):
    def __init__(self, parent):
        super.__init__(parent)

    def execute(self, node: iCodeNodeIF):
        routine_id = node.get_attribute('ID')
        routine_code: str = routine_id.get_attribute('ROUTINE_CODE')
        if routine_code == 'DECLARED':
            call_exec = CallDeclaredExecutor(self)
        else:
            call_exec = CallStandardExecutor(self)

        self.increment_exec_count()
        return call_exec.execute(node)


class CallDeclaredExecutor(CallExecutor):

    def __init__(self, parent):
        super.__init__(parent)

    def execute(self, node: iCodeNodeIF):
        routine_id: SynTabEntryIF = node.get_attribute('ID')
        new_ar: ActivationRecordIF = create_active_recode(routine_id)

        if len(node.get_children()) > 0:
            prms_node: iCodeNodeIF = node.get_children()[0]
            actual_nodes: list = prms_node.get_children()
            formal_ids: list = routine_id.get_attribute('ROUTINE_PARMS')
            self.execute_actual_parameters(actual_nodes, formal_ids, new_ar)

        self.runtime_stack.push(new_ar)
        self.send_call_message(node, routine_id.get_name())

        icode: iCodeIF = routine_id.get_attribute('ROUTINE_ICODE')
        root_node: iCodeNodeIF = icode.get_root()

        statement_exec = StatementExecutor(self)
        value = statement_exec.execute(root_node)

        self.runtime_stack.pop()
        self.send_return_message(node, routine_id.get_name())
        return value

    def execute_actual_parameters(self, actual_nodes: list, formal_ids: list, new_ar: ActivationRecordIF):
        expression_exec = ExpressionExecutor(self)
        assignment_exec = AssignmentExecutor(self)

        for i in range(len(formal_ids)):
            formal_id: SynTabEntryIF = formal_ids[i]
            formal_defn: Definition = formal_id.get_definition()
            formal_cell: CellIF = new_ar.get_cell(formal_id.get_name())
            actual_node: iCodeNodeIF = actual_nodes[i]

            if formal_defn == Definition.VAR_PARM:
                formal_type: TypeSpec = formal_id.get_typespec()
                value_type: TypeSpec = actual_node.get_typespec().base_type()
                value = expression_exec.execute(actual_node)
                assignment_exec.assign_value(actual_node, formal_id, formal_cell, formal_type, value, value_type)
            else:
                actual_cell: CellIF = expression_exec.execute_value(actual_node)
                formal_cell.value = actual_cell


class CallStandardExecutor(CallExecutor):
    def __init__(self, parent):
        expression_exec = None
        super.__init__(parent)

    def execute(self, node: iCodeNodeIF):
        routine_id = node.get_attribute('ID')
        routine_code: str = routine_id.get_attribute('ROUTINE_CODE')
        typespec: TypeSpec = node.get_typespec()
        self.expression_exec = ExpressionExecutor(self)
        actual_node: iCodeNodeIF = None

        if len(node.get_children()) > 0:
            prms_node: iCodeNodeIF = node.get_children()[0]
            actual_node = prms_node.get_children()[0]

        if routine_code == 'READ' or routine_code == 'READLN':
            return self.execute_read_readln(node, routine_code)
        elif routine_code == 'WRITE' or routine_code == 'WRITELN':
            return self.exec_write_writeln(node, routine_code)
        elif routine_code == 'EOF' or routine_code == 'EOLN':
            return self.exec_eof_eoln(node, routine_code)
        elif routine_code == 'ABS' or routine_code == 'SQR':
            return self.exec_abs_sqr(node, routine_code, actual_node)
        elif routine_code in ['ARCTAN', 'COS', 'EXP', 'LN', 'SIN', 'SQRT']:
            return self.exec_arctan_cos_exp_ln_sin_sqrt(node, routine_code, actual_node)
        elif routine_code == 'PRED' or routine_code == 'SUCC':
            return self.exec_pred_succ(node, routine_code, actual_node, typespec)
        elif routine_code == 'CHR':
            return self.exec_chr(node, routine_code, actual_node)
        elif routine_code == 'ODD':
            return self.exec_odd(node, routine_code, actual_node)
        elif routine_code == 'ORD':
            return self.exec_ord(node, routine_code, actual_node)
        elif routine_code == 'ROUND' or routine_code == 'TRUNC':
            return self.exec_round_trunc(node, routine_code, actual_node)
        return None

    def execute_read_readln(self, call_node: iCodeNodeIF, routine_code: str):
        if len(call_node.get_children()) > 0:
            prms_node: iCodeNodeIF = call_node.get_children()[0]
        else:
            prms_node: iCodeNodeIF = None

        if prms_node is not None:
            actuals: list = prms_node.get_children()
            for actual_node in actuals:
                typespec: TypeSpec = actual_node.get_typespec()
                basetype: TypeSpec = typespec.base_type()
                variable_cell: CellIF = self.expression_exec(actual_node)

                try:
                    if basetype == Predefined.integer_type:
                        token = self.standard_in.next_token()
                        value = int(self.parse_number(token, basetype))
                    elif basetype == Predefined.real_type:
                        token = self.standard_in.next_token()
                        value = float(self.parse_number(token, basetype))
                    elif basetype == Predefined.boolean_type:
                        token = self.standard_in.next_token()
                        value = self.parse_boolean(token)
                    elif basetype == Predefined.char_type:
                        ch = self.standard_in.next_ch()
                        if ch == Source.EOL or ch == Source.EOF:
                            ch = ' '
                        value = ch
                    else:
                        raise ValueError()

                except ValueError:
                    self.error_handler.flag(call_node, 'INVALID_INPUT', self)
                    if basetype == Predefined.real_type:
                        value = 0.0
                    elif basetype == Predefined.char_type:
                        value = ' '
                    elif basetype == Predefined.boolean_type:
                        value = False
                    else:
                        value = 0

                value = self.check_range(call_node, typespec, value)
                variable_cell.value = value
                actual_id: SynTabEntryIF = actual_node.get_attribute('ID')

                self.send_assign_message(call_node, actual_id.get_name(), value)

        if routine_code == 'READLN':
            try:
                self.standard_in.is_skip_to_next_line()
            except:
                self.error_handler.flag(call_node, 'INVALID_INPUT', self)

        return None

    def parse_number(self, token, typespec: TypeSpec):
        token_type = token.type
        sign = None

        if token_type == 'PLUS' or token_type == 'MINUS':
            sign = token_type
            token = self.standard_in.next_token()
            token_type = token.type

        value = token.value
        if token_type == PTT.INTEGER:
            if sign == 'MINUS':
                value = - int(token.value)

            if typespec == Predefined.integer_type:
                return int(value)
            else:
                return float(value)
        if token_type == PTT.REAL:
            if sign == 'MINUS':
                value = - float(value)

            return float(value)

        raise ValueError

    @staticmethod
    def parse_boolean(token):
        if token.value.lower() == 'true':
            return True
        elif token.value.lower() == 'false':
            return False
        raise ValueError

    def exec_write_writeln(self, call_node: iCodeNodeIF, routine_code: str):
        if len(call_node.get_children()) > 0:
            prms_node: iCodeNodeIF = call_node.get_children()[0]
        else:
            prms_node: iCodeNodeIF = None

        if prms_node is not None:
            actuals: list = prms_node.get_children()
            for write_prm_node in actuals:
                children: list = write_prm_node.get_children()
                expr_node: iCodeNodeIF = children[0]
                data_type: TypeSpec = expr_node.get_typespec().basetype()

                typecode: str = 's'
                if data_type == Predefined.integer_type:
                    typecode = 'd'
                elif data_type == Predefined.real_type:
                    typecode = 'f'
                elif data_type == Predefined.boolean_type:
                    typecode = 's'
                elif data_type == Predefined.char_type:
                    typecode = 'c'

                value = self.expression_exec.execute(expr_node)

                if data_type == Predefined.char_type and isinstance(value, str):
                    value = value[0]

                self.standard_out.print(str(value), end='')

        if routine_code == 'WRITELN':
            # \n
            self.standard_out.print('')

        return None

    def exec_eof_eoln(self, call_node: iCodeNodeIF, routine_code: str):
        try:
            if rotuine_code == 'EOF':
                return self.standard_in.at_eof()
            else:
                return self.standard_in.at_eol()
        except:
            self.error_handler.flag(call_node, 'INVALID_INPUT', self)
            return True


    def exec_abs_sqr(self, call_node: iCodeNodeIF, routine_code: str, actual_code: iCodeNodeIF):
        arg_value = self.expression_exec.execute(actual_node)
        if isinstance(arg_value, int):
            value = int(arg_value)
            if routine_code == 'ABS':
                return int(math.fabs(value))
            else:
                return value * value
        else:
            value = float(arg_value)
            if routine_code == 'ABS':
                return math.fabs(value)
            else:
                return value * value

    def exec_arctan_cos_exp_ln_sin_sqrt(self, call_node: iCodeNodeIF, routine_code: str, actual_node: iCodeNodeIF):
        arg_value = self.expression_exec.execute(actual_node)
        value = float(arg_value)
        if routine_code == 'ARCTAN':
            return math.atan(value)
        elif routine_code == 'COS':
            return math.cos(value)
        elif routine_code == 'EXP':
            return math.exp(value)
        elif routine_code == 'SIN':
            return math.sin(value)
        elif routine_code == 'LN':
            if value > 0.0:
                return math.log(value, 2)
            else:
                self.error_handler.flag(call_node, 'INVALID_STANDARD_FUNCTION_ARGUMENT', self)
                return 0.0
        elif routine_code == 'SQRT':
            if value > 0.0:
                return math.sqrt(value)
            else:
                self.error_handler.flag(call_node, 'INVALID_STANDARD_FUNCTION_ARGUMENT', self)
        return 0.0

    def exec_pred_succ(self, call_node: iCodeNodeIF, routine_code: str, actual_node: iCodeNodeIF, typespec: TypeSpec):
        value = int(self.expression_exec.execute(actual_node))
        if routine_code == 'PRED':
            new_value = value - 1
        else:
            new_value = value + 1
        new_value = self.check_range(call_node, typespec, new_value)
        return new_value


    def exec_chr(self, call_node: iCodeNodeIF, routine_code: str, actual_node: iCodeNodeIF):
        value = self.expression_exec.execute(actual_node)
        ch = str(value)
        return ch

    def exec_odd(self, call_node: iCodeNodeIF, routine_code: str, actual_node: iCodeNodeIF):
        value = int(self.expression_exec.execute(actual_node))
        return value % 2 == 1

    def exec_ord(self, call_node: iCodeNodeIF, routine_code: str, actual_node: iCodeNodeIF):
        value = self.expression_exec.execute(actual_node)
        if isinstance(value, str):
            return int(value[0])
        else:
            return int(value)

    def exec_round_trunc(self, call_node: iCodeNodeIF, routine_code: str, actual_node: iCodeNodeIF):
        value = float(self.expression_exec.execute(actual_node))
        if routine_code == 'ROUND':
            if value > 0.0:
                value = int(value + 0.5)
            else:
                value = int(value - 0.5)
        else:
            value = int(value)

        return value
