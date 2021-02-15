
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
#
# From https://twistedmatrix.com/documents/current/_downloads/simpleserv.py

# NOTE: pyrollbar requires both `Twisted` and `treq` packages to be installed

from twisted.internet import reactor, protocol

import rollbar


def bar(p):
    # These local variables will be sent to Rollbar and available in the UI
    a = 33
    b = a * 5
    baz()


def foo():
    hello = 'world'
    bar(hello)


class Echo(protocol.Protocol):
    """This is just about the simplest possible protocol"""

    def dataReceived(self, data):
        "As soon as any data is received, write it back."

        # Cause an uncaught exception to be sent to Rollbar
        foo()
        self.transport.write(data)


def main():
    rollbar.init('ACCESS_TOKEN', environment='test', handler='twisted')

    """This runs the protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = Echo
    reactor.listenTCP(8000, factory)
    reactor.run()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
