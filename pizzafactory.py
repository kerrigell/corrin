#!/usr/bin/env python
#coding:utf-8
import spyne
from spyne.application import Application
from spyne.decorator import srpc
from spyne.service import ServiceBase
from spyne.model.complex import Iterable
from spyne.model.primitive import UnsignedInteger
from spyne.model.primitive import String
from spyne.server.wsgi import WsgiApplication
from spyne.protocol.json import JsonDocument
from spyne.protocol.http import HttpRpc
from spyne.protocol.soap.soap11 import Soap11


class HelloWorldService(ServiceBase):
# '''sskdjf谁看得见发牢骚降低非'''
    @srpc(String, UnsignedInteger, _returns=Iterable(String))
    def say_hello(name, times):
        for i in xrange(times):
            yield 'Hello,%s' % name


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('spyne.protocol.xml').setLevel(logging.DEBUG)
    application = Application([HelloWorldService], 'spyne.examples.hello.http',
                              in_protocol=Soap11(validator='lxml'),
                              out_protocol=Soap11()
                              #in_protocol=HttpRpc(validator='soft'),
                              #out_protocol=JsonDocument(ignore_wrappers=None)
    )
    wsgi_application = WsgiApplication(application)
    server = make_server('127.0.0.1', 8000, wsgi_application)
    logging.info("listening to http://127.0.0.1:8000")
    logging.info("wsdl is at: http://localhost:8000/?wsdl")
    server.serve_forever()
    input('slkdjf')
    











