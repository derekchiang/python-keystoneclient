# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy

from keystoneclient import access
from keystoneclient import exceptions
from keystoneclient.tests.v3 import client_fixtures
from keystoneclient.tests.v3 import utils


class ServiceCatalogTest(utils.TestCase):
    def setUp(self):
        super(ServiceCatalogTest, self).setUp()
        self.AUTH_RESPONSE_BODY = client_fixtures.AUTH_RESPONSE_BODY
        self.RESPONSE = utils.TestResponse({
            "headers": client_fixtures.AUTH_RESPONSE_HEADERS
        })

        self.north_endpoints = {'public':
                                'http://glance.north.host/glanceapi/public',
                                'internal':
                                'http://glance.north.host/glanceapi/internal',
                                'admin':
                                'http://glance.north.host/glanceapi/admin'}

        self.south_endpoints = {'public':
                                'http://glance.south.host/glanceapi/public',
                                'internal':
                                'http://glance.south.host/glanceapi/internal',
                                'admin':
                                'http://glance.south.host/glanceapi/admin'}

    def test_building_a_service_catalog(self):
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        self.assertEqual(sc.url_for(service_type='compute'),
                         "https://compute.north.host/novapi/public")
        self.assertEqual(sc.url_for(service_type='compute',
                                    endpoint_type='internal'),
                         "https://compute.north.host/novapi/internal")

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for, "region",
                          "South", service_type='compute')

    def test_service_catalog_endpoints(self):
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        public_ep = sc.get_endpoints(service_type='compute',
                                     endpoint_type='public')
        self.assertEqual(public_ep['compute'][0]['region'], 'North')
        self.assertEqual(public_ep['compute'][0]['url'],
                         "https://compute.north.host/novapi/public")

    def test_service_catalog_regions(self):
        self.AUTH_RESPONSE_BODY['token']['region_name'] = "North"
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', endpoint_type='public')
        self.assertEqual(url, "http://glance.north.host/glanceapi/public")

        self.AUTH_RESPONSE_BODY['token']['region_name'] = "South"
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog
        url = sc.url_for(service_type='image', endpoint_type='internal')
        self.assertEqual(url, "http://glance.south.host/glanceapi/internal")

    def test_service_catalog_empty(self):
        # We need to do a copy.deepcopy here since
        # dict(self.AUTH_RESPONSE_BODY) or self.AUTH_RESPONSE_BODY.copy() will
        # only do a shadowcopy and sc_empty['token']['catalog'] will still be a
        # reference to self.AUTH_RESPONSE_BODY so setting it to empty will fail
        # the other tests that needs a service catalog.
        sc_empty = copy.deepcopy(self.AUTH_RESPONSE_BODY)
        sc_empty['token']['catalog'] = []
        auth_ref = access.AccessInfo.factory(self.RESPONSE, sc_empty)
        self.assertRaises(exceptions.EmptyCatalog,
                          auth_ref.service_catalog.url_for,
                          service_type='image',
                          endpoint_type='internalURL')

    def test_service_catalog_get_endpoints_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        endpoints = sc.get_endpoints(service_type='image', region_name='North')
        self.assertEqual(len(endpoints), 1)
        for endpoint in endpoints['image']:
            self.assertEqual(endpoint['url'],
                             self.north_endpoints[endpoint['interface']])

        endpoints = sc.get_endpoints(service_type='image', region_name='South')
        self.assertEqual(len(endpoints), 1)
        for endpoint in endpoints['image']:
            self.assertEqual(endpoint['url'],
                             self.south_endpoints[endpoint['interface']])

        endpoints = sc.get_endpoints(service_type='compute')
        self.assertEqual(len(endpoints['compute']), 3)

        endpoints = sc.get_endpoints(service_type='compute',
                                     region_name='North')
        self.assertEqual(len(endpoints['compute']), 3)

        endpoints = sc.get_endpoints(service_type='compute',
                                     region_name='West')
        self.assertEqual(len(endpoints['compute']), 0)

    def test_service_catalog_url_for_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', region_name='North')
        self.assertEqual(url, self.north_endpoints['public'])

        url = sc.url_for(service_type='image', region_name='South')
        self.assertEqual(url, self.south_endpoints['public'])

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for,
                          service_type='image', region_name='West')

    def test_servcie_catalog_get_url_region_names(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        urls = sc.get_urls(service_type='image')
        self.assertEqual(len(urls), 2)

        urls = sc.get_urls(service_type='image', region_name='North')
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], self.north_endpoints['public'])

        urls = sc.get_urls(service_type='image', region_name='South')
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], self.south_endpoints['public'])

        urls = sc.get_urls(service_type='image', region_name='West')
        self.assertIsNone(urls)

    def test_service_catalog_param_overrides_body_region(self):
        self.AUTH_RESPONSE_BODY['token']['region_name'] = "North"
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image')
        self.assertEqual(url, self.north_endpoints['public'])

        url = sc.url_for(service_type='image', region_name='South')
        self.assertEqual(url, self.south_endpoints['public'])

        endpoints = sc.get_endpoints(service_type='image')
        self.assertEqual(len(endpoints['image']), 3)
        for endpoint in endpoints['image']:
            self.assertEqual(endpoint['url'],
                             self.north_endpoints[endpoint['interface']])

        endpoints = sc.get_endpoints(service_type='image', region_name='South')
        self.assertEqual(len(endpoints['image']), 3)
        for endpoint in endpoints['image']:
            self.assertEqual(endpoint['url'],
                             self.south_endpoints[endpoint['interface']])
