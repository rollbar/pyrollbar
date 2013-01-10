"""
Unit tests
"""
from django.test import TestCase
from django.conf import settings

class BasicTests(TestCase):
    def test_configuration(self):
        """
        Test that the configuration is sane.
        """
        self.assertTrue('RATCHET' in dir(settings),
            msg='The RATCHET setting is not present.')
        self.assertTrue(settings.RATCHET.get('access_token'),
            msg='The RATCHET["access_token"] setting is blank.')
        
