import logging
import os

from sage.util import parse_URL
from clients import OverrideClient, TransportFactory

log = logging.getLogger("sage.aviary.locator")

class AviaryLocator(object):    
    def __init__(self, datadir, locator_uri,
                 key="", cert="", root_cert="", domain_verify=True):
        '''
        Initialize AviaryLocator so that get_endpoints may be used.
       
        datadir -- the directory containing a wsdl file for the locator

        locator_uri -- the URI used to the Aviary locator.
        There are sane defaults for scheme, port and path so only
        the hostname is required.  Defaults are http, 9000, and 
        'services/locator/locate' respectively.
        '''
        self.transport = TransportFactory(key, cert, root_cert, domain_verify)
        self.scheme, self.locator_uri = self._get_uri(locator_uri)
        self.datadir = datadir
        self.wsdl = "file:" + os.path.join(self.datadir, "aviary-locator.wsdl")
        log.info("AviaryLocator:  locator URL set to %s" % self.locator_uri)

    def _get_uri(self, locator):
        uri = parse_URL(locator)
        # Fill in scheme, port, path if they are blank
        if uri.scheme is None:
            uri.scheme = "http"
        if uri.port is None:
            uri.port = "9000"
        if uri.path is None:
            uri.path = "services/locator/locate"
        return uri.scheme, str(uri)
        
    def get_endpoints(self, resource, sub_type):
        '''
        Return endpoints from Aviary for the resource and sub_type.
        See documentation on the Aviary locator for information on
        legal values for resource and sub_type.
        '''
        the_transport = self.transport.get_transport(self.scheme)
        client = OverrideClient(self.wsdl, cache=None)
        client.set_options(location=self.locator_uri,
                           transport=the_transport)
        res_id = client.factory.create("ns0:ResourceID")
        res_id.resource = resource
        res_id.sub_type = sub_type
        res_id.name = None
        return client.service.locate(res_id)
