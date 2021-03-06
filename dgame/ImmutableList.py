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

    __slots__ = ('head', 'tail', 'size')

    def __init__(self, head, tail, size):
        self.head = head
        self.tail = tail
        self.size = size

    def __len__(self):
        return self.size

    def append(self, other):
        if other in self:
            return self

        return LinkedList(other, self, self.size + 1)

    def __iter__(self):
        return LinkedListIterator(self)

    def __repr__(self):
        return 'i[' + ', '.join(map(lambda x: repr(x), self)) + ']'

    def __contains__(self, item):
        return item in set(self)


END = LinkedList(None, None, 0)


def cons(elem, linked_list):
    return linked_list.append(elem)


def nil():
    return END
