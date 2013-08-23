# observer - basic observer pattern support classes
#
# Copyright 2013 Commons Machinery http://commonsmachinery.se/
#
# Authors: Peter Liljenberg <peter@commonsmachinery.se>
#
# Distributed under an GPLv2 license, please see LICENSE in the top dir.

import sys

# Set this to a function taking args (subject, event) to see everything sent
global_observer = None

def log_observer(subject, event):
    sys.stderr.write('{0}: {1}\n'.format(repr(subject), event))


class Event(object):
    def __init__(self, **kws):
        self.__dict__.update(kws)

    def __str__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.__dict__)


class Subject(object):
    def __init__(self):
        super(Subject, self).__init__()
        self._observers = []
        self._pending_deletions = []
        self._pending_additions = []
        self._pending_events = []
        self._notification_in_progress = False

    def register_observer(self, observer):
        """Register a new observer, which should be a function taking
        a single Event argument.

        If added while a notification is in progress, the observer
        will not recieve the current event.
        """

        assert observer not in self._observers

        if self._notification_in_progress:
            assert observer not in self._pending_additions
            self._pending_additions.append(observer)
        else:
            self._observers.append(observer)
            

    def unregister_observer(self, observer):
        """Unregister a previously registered observer.

        If called while a notification is in progress, the observer
        will recieve the current event before being removed.
        """

        if self._notification_in_progress:
            assert observer not in self._pending_deletions
            assert (observer in self._observers
                    or observer in self._pending_additions)

            self._pending_deletions.append(observer)
        else:
            assert observer in self._observers
            self._observers.remove(observer)


    def notify_observers(self, event):
        """Notify all observers about an event.

        If an event is already being notified, this event is queued
        and processed once all previous events have been completed.
        """

        if self._notification_in_progress:
            self._pending_events.append(event)
            return
        
        try:
            assert not self._pending_deletions
            assert not self._pending_additions

            self._notification_in_progress = True

            if global_observer:
                global_observer(self, event)

            for obs in self._observers:
                obs(event)
        finally:
            self._notification_in_progress = False

        # Process additions and deletions that resulted from this event

        if self._pending_additions:
            self._observers.extend(self._pending_additions)
            del self._pending_additions[:]

        if self._pending_deletions:
            for obs in self._pending_deletions:
                self._observers.remove(obs)
            del self._pending_deletions[:]
                
        # Process any further events that resulted from this event.
        # Doing it recursively is easier, and also means that if the
        # observers manage to set up an infinite loop of events, we'll
        # hit the recursion limit in Python eventually.

        if self._pending_events:
            ev = self._pending_events.pop(0)
            self.notify_observers(ev)


class AssertEvent(object):
    """Helper class for unit tests:

    Used this as a context manager to check that a certain sequence of
    events is notified by a subject:

    with AssertEvent(self, subject, EventClass1, EventClass2...):
        ...
    """
    
    def __init__(self, test, subject, *event_classes):
        self.test = test
        self.subject = subject
        self.expected = event_classes
        self.actual = []
        
    def _on_event(self, e):
        self.actual.append(e.__class__)

    def __enter__(self):
        self.subject.register_observer(self._on_event)

    def __exit__(self, exc_type, exc_value, traceback):
        self.subject.unregister_observer(self._on_event)

        if exc_type is None:
            self.test.assertSequenceEqual(self.expected, self.actual)

