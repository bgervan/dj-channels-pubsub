import queue


class SetQueue(queue.Queue):

    """
    Add item if it's not in the queue already
    """
    def _put(self, item):
        if item not in self.queue:
            self.queue.append(item)
