from collections import namedtuple, Iterator
from copy import deepcopy


class IListIterator(Iterator):
    def __init__(self, list):
        self.list = list

    def __next__(self):
        if self.list is END:
            raise StopIteration

        t = self.list.head
        self.list = self.list.tail
        return t


class ImmutableList:
    unique = set()

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
            return ImmutableList(other, self, set({other}))

        if other in self.unique:
            return self

        cp = deepcopy(self.unique)
        cp.add(other)
        return ImmutableList(other, self, cp)

    def __iter__(self):
        return IListIterator(self)

    def __repr__(self):
        return 'i[' + ', '.join(map(lambda x: repr(x), self)) + ']'


END = ImmutableList(None, None, unique=None)


def cons(elem, ilist):
    return ilist + elem


def IList():
    return END


def flatten(ilist):
    arr = []

    while ilist is not END:
        head = ilist.head
        arr.append(head)
        ilist = ilist.tail

    return arr


if __name__ == '__main__':
    print(IList())

    a = cons(3, cons(1, cons(2, IList())))

    print(len(a))

    print(a + 3)

    print(IList() + 1)

    print(flatten(a))

    print('T')
    for i in a:
        print(i)
