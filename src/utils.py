from collections import deque
from src.custom_exceptions import SimpleStackError


class SimpleStack:

    def __init__(self, stack_type):
        self.__stack = deque()
        self.__stack_type = stack_type

    def empty(self):
        return len(self.__stack) == 0

    def push(self, item):

        if not isinstance(item, self.__stack_type):
            raise TypeError(
                f'Expected type "{self.__stack_type.__name__}", '
                f'but received "{type(item).__name__}".'
            )
        self.__stack.append(item)

    def top(self):
        if not self.empty():
            return self.__stack[-1]

    def pop(self):
        if self.empty():
            raise SimpleStackError("Pop failed: Stack is empty.")
        return self.__stack.pop()
