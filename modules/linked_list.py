class LinkedList:
    def __init__(self):
        self.front = None
        self.size = 0

        # support for standard iteration
        self.iterator_count = 0
        self.iterator_pointer = None

    def __iter__(self):
        self.iterator_count = 0
        self.iterator_pointer = self.front
        return self

    def __next__(self):
        if self.iterator_count < self.size:
            self.iterator_count += 1
            self.iterator_pointer = self.iterator_pointer.next
            return self.iterator_pointer.pre.data
        else:
            raise StopIteration

    def __getitem__(self, item):
        # support negative indexing
        if item < 0:
            index = self.size + item

        if 0 <= item < self.size and self.size is not 0:
            get_point = self.front
            for i in range(0, item):
                get_point = get_point.next
            return get_point.data
        else:
            raise IndexError("linked list accessor index out of range")

    def __len__(self):
        return self.size

    def __contains__(self, item):
        for entry in self:
            if entry == item:
                return True
        return False

    def add(self, data, index: int = -1, prevent_duplicates: bool = False):
        # check for duplicate insertion if it is being prevented
        if prevent_duplicates:
            for item in self:
                if item == data:
                    return False

        # support negative indexing
        if index < 0:
            index = self.size + index + 1

        if 0 <= index <= self.size or self.size == 0:
            insertion_point = self.front
            for i in range(0, index):
                insertion_point = insertion_point.next
            node = Node(insertion_point, data)
            if self.size == 0 or index == 0:
                self.front = node
            self.size += 1
            return True
        else:
            raise IndexError("linked list insertion index out of range")

    def remove(self, index: int):
        # support negative indexing
        if index < 0:
            index = self.size + index

        if 0 <= index < self.size and self.size is not 0:
            removal_point = self.front
            for i in range(0, index):
                removal_point = removal_point.next
            if index == 0:
                self.front = removal_point.next
            data = removal_point.delete()
            self.size -= 1
            return data
        else:
            raise IndexError("linked list removal index out of range")

    def remove_object(self, data):
        if self.size is not 0:
            i = 0
            for item in self:
                if item == data:
                    self.remove(i)
                    return True
                i += 1
            return False
        else:
            raise IndexError("linked list is empty")


class Node:
    def __init__(self, insertion_point, data):
        if insertion_point is None:
            self.pre = self
            self.next = self
        else:
            # attach
            self.pre = insertion_point.pre
            self.next = insertion_point

            # integrate
            insertion_point.pre = self
            self.pre.next = self

        self.data = data

    def delete(self):
        self.pre.next = self.next
        self.next.pre = self.pre
        return self.data
