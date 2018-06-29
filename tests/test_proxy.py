from unittest.mock import patch
from urllib.parse import urlencode

from ..proxy import ConfigProxy


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


class TestProxy(NIOTestCase):

    def test_get_version(self):
        proxy = ConfigProxy()
        with patch("{}.requests".format(ConfigProxy.__module__)) \
                as request_patch:
            proxy.get_version("api", "config_id", "token")
            headers = proxy._get_headers("token")

            test_headers = {
                "authorization": "apikey token",
                "content-type": "application/json"
            }
            self.assertEqual(headers, test_headers)

            desired_url = "api/config_id/versions/latest"
            request_patch.get.assert_called_with(desired_url,
                                                 headers=headers)

    def test_load_configuration(self):
        proxy = ConfigProxy()
        with patch("{}.requests".format(ConfigProxy.__module__)) \
                as request_patch:
            proxy.load_configuration("api",
                                     "config_id",
                                     "config_version_id",
                                     "token")
            headers = proxy._get_headers("token")

            test_headers = {
                "authorization": "apikey token",
                "content-type": "application/json"
            }
            self.assertEqual(headers, test_headers)

            desired_url = "api/config_id/versions/config_version_id"
            request_patch.get.assert_called_with(desired_url,
                                                 headers=headers)
