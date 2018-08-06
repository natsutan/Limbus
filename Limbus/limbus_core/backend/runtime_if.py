import sys
from abc import ABCMeta, abstractmethod

from ..message import Message, MessageType
from .activation_record_if import ActivationRecordIF


class CellIF(metaclass=ABCMeta):
    @property
    @abstractmethod
    def value(self):
        raise NotImplementedError()

    @value.setter
    @abstractmethod
    def value(self, v):
        raise NotImplementedError()


class RuntimeStackIF(metaclass=ABCMeta):
    def __init__(self):
        self.records: list = []

    @abstractmethod
    def get_topmost(self, nesting_level: int):
        raise NotImplementedError()

    @abstractmethod
    def current_nesting_level(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def pop(self):
        raise NotImplementedError()

    @abstractmethod
    def push(self, ar):
        raise NotImplementedError()


class RuntimeDisplayIF(metaclass=ABCMeta):
    @abstractmethod
    def get_active_record(self, nesting_level: int) -> ActivationRecordIF:
        raise NotImplementedError()

    @abstractmethod
    def call_update(self, nesting_level: int, ar: ActivationRecordIF):
        raise NotImplementedError()

    @abstractmethod
    def return_update(self, nesting_level: int):
        raise NotImplementedError()


class RuntimeErrorCode:
    UNINITIALIZED_VALUE = "Uninitialized value"
    VALUE_RANGE = "Value out of range"
    INVALID_CASE_EXPRESSION_VALUE = "Invalid CASE expression value"
    DIVISION_BY_ZERO = "Division by zero"
    INVALID_STANDARD_FUNCTION_ARGUMENT = "Invalid standard function argument"
    INVALID_INPUT = "Invalid input"
    STACK_OVERFLOW = "Runtime stack overflow"
    UNIMPLEMENTED_FEATURE = "Unimplemented runtime feature"

    def __init__(self):
        self.message: str = ""

    def runtime_error_code(self, message: str):
        self.message = message


class RuntimeErrorHandler:
    MAX_ERRORS = 5
    error_count = 0

    def flag(self, node, error_code: RuntimeErrorCode, backend):

        while (not (node is None)) and node.get_attribute('LINE') is None:
            node = node.get_parent()

        msg = Message(MessageType.RUNTIME_ERROR, (error_code.message, node.get_attribute('LINE')))
        backend.send_message(msg)

        self.error_count += 1
        if self.MAX_ERRORS < self.error_count:
            print('*** ABORTED AFTER TOO MANY RUNTIME ERRORS.')
            sys.exit(-1)
