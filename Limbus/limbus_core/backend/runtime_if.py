from abc import ABCMeta, abstractmethod

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


