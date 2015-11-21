import os
from suds.client import Client
from sage.util import ObjectPool
from suds.transport.https import HttpAuthenticated
from sage.https import HTTPSClientCertTransport

try:
    from sage.https_full import HTTPSFullCertTransport
    has_full_cert = True
    technology = sage.https_full.technology
except:
    has_full_cert = False

class TransportFactory(object):
    def __init__(self, key="", cert="", root_cert="", domain_verify=True):
        self.key = key
        self.cert = cert
        self.root_cert = root_cert
        self.domain_verify = domain_verify
        self.server_validation_possible = has_full_cert

    def log_details(self, log, where="HTTPSClient"):
        if self.root_cert == "":
            log.info("%s: no root certificate file specified, "\
                "using client validation only for ssl connections." % where)

        elif not self.server_validation_possible:
            log.info("%s: server certificate validation not "\
                     "supported, using client validation "\
                     "only for ssl connections." % where)
        else:
            log.info("%s: using client and server "\
                     "certificate validation for ssl connections, "\
                     "solution is %s" % (where, clients.technology))

            log.info("%s: verify server domain against "\
                     "certificate during validation (%s)" \
                     % (where, self.domain_verify))

    def get_transport(self, scheme):
        if scheme == "https":
            if not os.path.isfile(self.key):
                raise Exception("Private key file "\
                                "for ssl communication with Aviary not found")
            if not os.path.isfile(self.cert):
                raise Exception("Client certificate file "\
                                "for ssl communication with Aviary not found")
            if self.root_cert != "" and self.server_validation_possible:
                if not os.path.isfile(self.root_cert):
                    raise Exception("Root certificate file "\
                                    "for Aviary server validation not found")
                the_transport = HTTPSFullCertTransport(self.key, 
                                                       self.cert, 
                                                       self.root_cert,
                                                       self.domain_verify)
            else:
                the_transport = HTTPSClientCertTransport(self.key, self.cert)
        else:
            # this is the default transport when none is specified
            the_transport = HttpAuthenticated()
        return the_transport

try:
    # Some of this stuff does not exist pre suds 0.4.1
    # Make it work anyway for testing on such hosts by
    # declaring simple OverridesPlugin in the exception case.
    from suds.plugin import MessagePlugin
    from suds.sax.attribute import Attribute
    class OverridesPlugin(MessagePlugin):
        '''
        Plugin which allows optional addition of attributes
        to the suds message after marshalling.
        '''
        def __init__(self):
            self.set_attributes = False
            self.attributes = dict()

        def marshalled(self, context):
            if self.set_attributes:
                sj_body = context.envelope.getChild('Body')[0]
                for k,v in self.attributes.iteritems():
                    sj_body.attributes.append(Attribute(k, v))

except:
    class OverridesPlugin(object):
        def __init__(self):
            self.set_attributes = False

class OverrideClient(Client):
    '''
    Instantiate a Client object with an OverridesPlugin and
    retain a pointer to the plugin so that it can be controlled.
    '''
    def __init__(self, *args, **kwargs):
        self.override = OverridesPlugin()
        try:
            super(OverrideClient, self).__init__(plugins=[self.override], *args, **kwargs)
        except:
            super(OverrideClient, self).__init__(*args, **kwargs)

    def set_enable_attributes(self, truth):
        '''
        Set the flag that controls whether extra attributes are marshalled.

        The attribute set is specified through the set_attributes() method.
        If 'truth' is True, then service calls made through this client
        will have the extra attributes appended to the attribute set of service
        request.
        '''
        self.override.set_attributes = truth

    def set_attributes(self, attrs):
        '''
        Specify extra attributes to append to the attribute set
        of service requests made through this client.

        The extra attributes will be added if set_enable_attributes()
        has been called with a value of True sometime prior to the
        time of a request.
        '''
        self.override.attributes = attrs

class ClientPool(ObjectPool):
    def __init__(self, wsdl, max_size):
        super(ClientPool, self).__init__(max_size)
        self.wsdl = wsdl

    def create_object(self):
        return OverrideClient(self.wsdl, cache=None)
