import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from datetime import datetime

class Bitrix24HandlerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_token = "ijtf0dz352qh5t0ganhowoqy66miijxj"
        self.url = "/myapp/bitrix24_handler/"

    @patch('myapp.views.GoogleAdsClient')
    def test_valid_lead_add_event(self, MockGoogleAdsClient):
        """Test a valid ONCRMLEADADD event with GCLID"""
        MockGoogleAdsClient.load_from_storage.return_value = MockGoogleAdsClient
        mock_conversion_upload_service = MockGoogleAdsClient.get_service.return_value
        mock_conversion_upload_service.upload_click_conversions.return_value.partial_failure_error = None

        payload = {
            "auth": {"application_token": self.valid_token},
            "event": "ONCRMLEADADD",
            "data": {
                "FIELDS": {
                    "ID": "123",
                    "TITLE": "Test Lead",
                    "STATUS": "NEW",
                    "EMAIL": [{"VALUE": "test@example.com"}],
                    "PHONE": [{"VALUE": "+123456789"}],
                    "CURRENCY": "USD",
                    "AMOUNT": 100.0,
                    "DATE_CREATE": "2025-01-27 12:00:00"
                },
                "GCLID": "test-gclid-123"
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json().get("status", ""))

        mock_conversion_upload_service.upload_click_conversions.assert_called_once()

    @patch('myapp.views.GoogleAdsClient')
    def test_valid_deal_add_event(self, MockGoogleAdsClient):
        """Test a valid ONCRMDEALADD event with GCLID"""
        MockGoogleAdsClient.load_from_storage.return_value = MockGoogleAdsClient
        mock_conversion_upload_service = MockGoogleAdsClient.get_service.return_value
        mock_conversion_upload_service.upload_click_conversions.return_value.partial_failure_error = None

        payload = {
            "auth": {"application_token": self.valid_token},
            "event": "ONCRMDEALADD",
            "data": {
                "FIELDS": {
                    "ID": "987",
                    "TITLE": "Test Deal",
                    "STAGE_ID": "DEAL_WON",
                    "AMOUNT": 200.0,
                    "CURRENCY": "USD"
                },
                "GCLID": "test-gclid-456"
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json().get("status", ""))

        mock_conversion_upload_service.upload_click_conversions.assert_called_once()

    def test_invalid_token(self):
        """Test the handler with an invalid token"""
        payload = {
            "auth": {"application_token": "invalid-token"},
            "event": "ONCRMLEADADD",
            "data": {
                "FIELDS": {
                    "ID": "123",
                    "TITLE": "Test Lead",
                    "STATUS": "NEW"
                },
                "GCLID": "test-gclid-123"
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("Unauthorized", response.json().get("error", ""))

    def test_missing_gclid(self):
        """Test missing GCLID in payload"""
        payload = {
            "auth": {"application_token": self.valid_token},
            "event": "ONCRMLEADADD",
            "data": {
                "FIELDS": {
                    "ID": "123",
                    "TITLE": "Test Lead",
                    "STATUS": "NEW"
                }
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("GCLID not found", response.json().get("error", ""))

    def test_invalid_content_type(self):
        """Test invalid content type"""
        payload = "invalid=data&format=true"
        response = self.client.post(
            self.url,
            data=payload,
            content_type="text/plain"
        )

        self.assertEqual(response.status_code, 415)
        self.assertIn("Unsupported Media Type", response.json().get("error", ""))

    @patch('myapp.views.GoogleAdsClient')
    def test_valid_lead_delete_event(self, MockGoogleAdsClient):
        """Test valid ONCRMLEADDELETE event with GCLID"""
        MockGoogleAdsClient.load_from_storage.return_value = MockGoogleAdsClient
        mock_conversion_upload_service = MockGoogleAdsClient.get_service.return_value
        mock_conversion_upload_service.upload_click_conversions.return_value.partial_failure_error = None

        payload = {
            "auth": {"application_token": self.valid_token},
            "event": "ONCRMLEADDELETE",
            "data": {
                "FIELDS": {
                    "ID": "123"
                },
                "GCLID": "test-gclid-123"
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json().get("status", ""))

        mock_conversion_upload_service.upload_click_conversions.assert_called_once()

    @patch('myapp.views.GoogleAdsClient')
    def test_valid_deal_delete_event(self, MockGoogleAdsClient):
        """Test valid ONCRMDEALDELETE event with GCLID"""
        MockGoogleAdsClient.load_from_storage.return_value = MockGoogleAdsClient
        mock_conversion_upload_service = MockGoogleAdsClient.get_service.return_value
        mock_conversion_upload_service.upload_click_conversions.return_value.partial_failure_error = None

        payload = {
            "auth": {"application_token": self.valid_token},
            "event": "ONCRMDEALDELETE",
            "data": {
                "FIELDS": {
                    "ID": "987"
                },
                "GCLID": "test-gclid-456"
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json().get("status", ""))

        mock_conversion_upload_service.upload_click_conversions.assert_called_once()
