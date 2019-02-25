from collections import Iterator
from copy import deepcopy


class LinkedListIterator(Iterator):
    def __init__(self, linked_list):
        self.list = linked_list

    def __next__(self):
        if self.list is END:
            raise StopIteration

        t = self.list.head
        self.list = self.list.tail
        return t


class LinkedList:
    """ Immutable linked list with unique elements"""

    __slots__ = ('head', 'tail', 'unique')

    def __init__(self, head, tail, unique):
        self.head = head
        self.tail = tail
        self.unique = unique

    def __len__(self):
        if self.head is None:
            return 0

        return 1 + len(self.tail)

    def __add__(self, other):
        if self.unique is None:
            return LinkedList(other, self, {other})

        if other in self.unique:
            return self

        cp = deepcopy(self.unique)
        cp.add(other)
        return LinkedList(other, self, cp)

    def __iter__(self):
        return LinkedListIterator(self)

    def __repr__(self):
        return 'i[' + ', '.join(map(lambda x: repr(x), self)) + ']'


END = LinkedList(None, None, unique=None)


def cons(elem, linked_list):
    """ concatenate an element to an existing list """
    return linked_list + elem


def nil():
    """ return the empty list """
    return END
