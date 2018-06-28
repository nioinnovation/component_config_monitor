from unittest.mock import patch
from urllib.parse import urlencode

from ..proxy import ConfigProxy


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


class TestProxy(NIOTestCase):

    def test_requests_call(self):
        proxy = ConfigProxy()
        with patch("{}.requests".format(ConfigProxy.__module__)) \
                as request_patch:
            proxy.load_configuration("url", "token")
            headers = proxy._get_headers("token")

            test_headers = {
                "authorization": "apikey token",
                "content-type": "application/json"
            }
            self.assertEqual(headers, test_headers)

            request_patch.get.assert_called_with("url",
                                                 headers=headers)
