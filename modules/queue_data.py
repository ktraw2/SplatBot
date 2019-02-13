class Queue_Data:

    """
    Constructor for a Queue
    """
    def __init__(self, **metadata):
        self.queue = []
        self.metadata = metadata

    """
    Appends an unique element to the Queue
    
    Returns True if the element was successfully added
    Returns False if the element already exists in the Queue
    """
    def add_nondup(self, data):
        if data not in self.queue:
            self.queue.insert(0, data)
            return True
        return False

    """
    Appends an element to the Queue

    Appends the element regardless of it was already in the Queue
    """
    def add_dup(self, data):
        self.queue.insert(0, data)

    """
    Removes and returns the head of the Queue
    
    Returns False w/ null if there are no elements to pop
    Returns True w/ requested element if there was an element popped
    """
    def pop(self):
        if len(self.queue) > 0:
            return True, self.queue.pop(0)
        return False, None
    
    """
    Returns the size of the Queue
    """
    def size(self):
        return len(self.queue)

    """
    Returns and removes the first "num" elements in the Queue
    
    If there are less than "num" elements, will return False w/ null
    Otherwise will return True w/ the requested elements
    """
    def pop_num(self, num):
        num_elm_to_pop = num
        index = 0
        peek = []
        if len(self.queue) > 0:
            if index > num:
                return False, None
            for i in range(0, num_elm_to_pop):
                peek = [i, self.pop()[1]]
            return True, peek
