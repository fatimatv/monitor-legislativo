import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from legislative_monitor.congress import CongressClient, CongressSourceError


class PublicDocumentClient(CongressClient):
    def __init__(self):
        super().__init__()
        self.calls = []

    def _request(self, url, method="GET", body=None, headers=None):
        self.calls.append(headers or {})
        return b"%PDF-1.7 public", {"Content-Disposition": "attachment; filename=proyecto.pdf"}


class CongressDocumentTests(unittest.TestCase):
    def test_downloads_public_pdf_without_captcha_token(self):
        client = PublicDocumentClient()

        body, filename = client.download_document("https://api.congreso.gob.pe/spley-portal-service/archivo/123/pdf", "")

        self.assertTrue(body.startswith(b"%PDF"))
        self.assertEqual(filename, "attachment; filename=proyecto.pdf")
        self.assertEqual(client.calls, [{}])

    @patch("legislative_monitor.congress.urlopen", side_effect=ConnectionAbortedError(10053, "conexión cerrada"))
    def test_wraps_socket_abort_as_a_recoverable_source_error(self, _urlopen):
        client = CongressClient(max_retries=1)

        with self.assertRaises(CongressSourceError):
            client.download_document("https://api.congreso.gob.pe/spley-portal-service/archivo/123/pdf")

    @patch("legislative_monitor.congress.time.sleep")
    @patch("legislative_monitor.congress.urlopen")
    def test_does_not_retry_a_permanent_document_rejection(self, urlopen, _sleep):
        urlopen.side_effect = HTTPError("https://example.test/document.pdf", 406, "Not Acceptable", {}, None)
        client = CongressClient(max_retries=3)

        with self.assertRaises(CongressSourceError):
            client.download_document("https://example.test/document.pdf")

        self.assertEqual(urlopen.call_count, 1)
