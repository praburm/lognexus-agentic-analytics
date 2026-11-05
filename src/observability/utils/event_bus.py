from queue import Queue


class EventBus:
    def __init__(self):
        self.monitor_events = Queue()  # monitor → correlator
        self.incidents = Queue()       # correlator → rca
        self.rca_events = Queue()      # rca → downstream consumers
