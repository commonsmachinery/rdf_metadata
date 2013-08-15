# event - basic event signalling classes
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.


class Event(object):
    def __init__(self, callback, source = None):
        self.callback = callback
        self.source = source


class EventSource(object):
    def __init__(self):
        super(EventSource, self).__init__()
        self._events = []

    def connect_event(self, event):
        assert event not in self._events
        self._events.append(event)

    def signal_event(self, event_class, source, *args, **kwargs):
        for e in self._events:
            if ((e.source is None or e.source is source)
                and isinstance(e, event_class)):
                e.callback(e, source, *args, **kwargs)
