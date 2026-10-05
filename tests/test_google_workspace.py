import unittest

from legislative_monitor.google_workspace import GoogleWorkspace, SHEET_COLUMNS
from legislative_monitor.models import Analysis, Classification, Proposition


class FakeValues:
    def __init__(self, rows):
        self.rows = rows
        self.updated = []
        self.appended = []

    def get(self, **kwargs):
        return FakeRequest({"values": self.rows})

    def update(self, **kwargs):
        self.updated.append(kwargs)
        if kwargs["range"].endswith("A1"):
            self.rows = kwargs["body"]["values"]
        return FakeRequest({})

    def append(self, **kwargs):
        self.appended.append(kwargs)
        return FakeRequest({})


class FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeSpreadsheets:
    def __init__(self, rows):
        self.values_api = FakeValues(rows)

    def get(self, **kwargs):
        return FakeRequest({"sheets": [{"properties": {"title": "Iniciativas"}}]})

    def values(self):
        return self.values_api

    def batchUpdate(self, **kwargs):
        return FakeRequest({})


class FakeSheets:
    def __init__(self, rows):
        self.spreadsheet_api = FakeSpreadsheets(rows)

    def spreadsheets(self):
        return self.spreadsheet_api


def proposition():
    item = Proposition("00498-2026-2031-CD", 498, 2026, "D", None, "Redes sociales", "PRESENTADO", "", "", "https://official.example")
    item.classification = Classification(True, ["Plataformas y comercio digital"], "ALTA", "prueba")
    item.analysis = Analysis("HECHO NORMATIVO: prueba", "INTERPRETACIÓN: prueba", "ANALIZADO")
    return item


class GoogleWorkspaceTests(unittest.TestCase):
    def make_workspace(self, rows):
        workspace = object.__new__(GoogleWorkspace)
        workspace.sheet_id = "sheet"
        workspace.sheets = FakeSheets(rows)
        return workspace

    def test_inserts_when_identifier_is_missing(self):
        workspace = self.make_workspace([])
        workspace.upsert_sheet_row(proposition(), "https://drive.example", "https://pdf.example")
        values = workspace.sheets.spreadsheet_api.values_api
        self.assertEqual(len(values.appended), 1)

    def test_updates_existing_identifier_and_preserves_detection_date(self):
        old_row = [""] * len(SHEET_COLUMNS)
        old_row[SHEET_COLUMNS.index("ID DEL EXPEDIENTE")] = "00498-2026-2031-CD"
        old_row[SHEET_COLUMNS.index("FECHA DE DETECCIÓN")] = "2026-10-01T00:00:00+00:00"
        workspace = self.make_workspace([SHEET_COLUMNS, old_row])
        workspace.upsert_sheet_row(proposition(), "https://drive.example", "https://pdf.example")
        values = workspace.sheets.spreadsheet_api.values_api
        self.assertEqual(len(values.updated), 1)
        updated = values.updated[0]["body"]["values"][0]
        self.assertEqual(updated[SHEET_COLUMNS.index("FECHA DE DETECCIÓN")], "2026-10-01T00:00:00+00:00")
