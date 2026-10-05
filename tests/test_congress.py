import unittest

from legislative_monitor.congress import CongressClient


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
