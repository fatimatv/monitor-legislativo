from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Document, Proposition


SHEET_COLUMNS = [
    "PROPOSICIÓN LEGISLATIVA", "FECHA DE PRESENTACIÓN", "TÍTULO", "ESTADO PROCESAL", "PROPONENTE", "AUTORES",
    "LINK DE DESCARGA", "PRINCIPALES OBLIGACIONES", "IMPACTO EN EL ECOSISTEMA DIGITAL", "FECHA DE DETECCIÓN",
    "CATEGORÍA TEMÁTICA", "NIVEL DE RELEVANCIA", "FUNDAMENTO DE RELEVANCIA", "URL DEL EXPEDIENTE", "LINK CARPETA DRIVE",
    "ÚLTIMA ACTUALIZACIÓN", "ID DEL EXPEDIENTE", "URL DOCUMENTO ORIGINAL", "ESTADO DE PROCESAMIENTO",
]


class GoogleWorkspaceError(RuntimeError):
    pass


class GoogleWorkspace:
    def __init__(self, service_account_file: str, root_folder_id: str, sheet_id: str):
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise GoogleWorkspaceError("Faltan dependencias de Google; instale el proyecto.") from exc
        credentials = Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"],
        )
        self.drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
        self.sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        self.root_folder_id = root_folder_id
        self.sheet_id = sheet_id

    def _find_or_create_folder(self, name: str, parent_id: str, stable_key: str) -> str:
        query = f"'{parent_id}' in parents and trashed=false and appProperties has {{ key='monitor_key' and value='{stable_key}' }}"
        results = self.drive.files().list(q=query, fields="files(id,name)").execute().get("files", [])
        if results:
            return results[0]["id"]
        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id], "appProperties": {"monitor_key": stable_key}}
        return self.drive.files().create(body=metadata, fields="id").execute()["id"]

    def proposition_folder(self, proposition: Proposition) -> tuple[str, str]:
        year_folder = self._find_or_create_folder(str(proposition.parliamentary_period), self.root_folder_id, f"year:{proposition.parliamentary_period}")
        proposition_folder = self._find_or_create_folder(
            f"{proposition.official_id} - {proposition.title[:70]}", year_folder, f"proposition:{proposition.official_id}"
        )
        return proposition_folder, f"https://drive.google.com/drive/folders/{proposition_folder}"

    def upload_document(self, folder_id: str, document: Document) -> str:
        if not document.local_path:
            raise GoogleWorkspaceError("No se puede cargar un documento no descargado.")
        query = f"'{folder_id}' in parents and trashed=false and appProperties has {{ key='source_document_id' and value='{document.official_id}' }}"
        existing = self.drive.files().list(q=query, fields="files(id)").execute().get("files", [])
        if existing:
            return existing[0]["id"]
        from googleapiclient.http import MediaFileUpload
        metadata = {"name": Path(document.local_path).name, "parents": [folder_id], "appProperties": {"source_document_id": document.official_id, "sha256": document.sha256 or ""}}
        return self.drive.files().create(body=metadata, media_body=MediaFileUpload(document.local_path, mimetype="application/pdf"), fields="id").execute()["id"]

    def upsert_sheet_row(self, proposition: Proposition, drive_folder_url: str, download_link: str) -> None:
        worksheet = "Iniciativas"
        metadata = self.sheets.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        names = {sheet["properties"]["title"] for sheet in metadata.get("sheets", [])}
        if worksheet not in names:
            self.sheets.spreadsheets().batchUpdate(spreadsheetId=self.sheet_id, body={"requests": [{"addSheet": {"properties": {"title": worksheet}}}]}).execute()
        existing = self.sheets.spreadsheets().values().get(spreadsheetId=self.sheet_id, range=f"{worksheet}!A:Z").execute().get("values", [])
        if not existing:
            self.sheets.spreadsheets().values().update(spreadsheetId=self.sheet_id, range=f"{worksheet}!A1", valueInputOption="RAW", body={"values": [SHEET_COLUMNS]}).execute()
            existing = [SHEET_COLUMNS]
        header = existing[0]
        if header != SHEET_COLUMNS:
            raise GoogleWorkspaceError("La cabecera de Sheets no coincide con el esquema esperado; no se modifica para evitar corrupción.")
        row = proposition.sheet_row(drive_folder_url, download_link)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        row["ÚLTIMA ACTUALIZACIÓN"] = now
        values = [[row.get(column, "") for column in SHEET_COLUMNS]]
        id_index = SHEET_COLUMNS.index("ID DEL EXPEDIENTE")
        match = next(((index + 1, values_row) for index, values_row in enumerate(existing[1:], 2) if len(values_row) > id_index and values_row[id_index] == proposition.official_id), None)
        if match:
            match_row, previous_values = match
            detection_index = SHEET_COLUMNS.index("FECHA DE DETECCIÓN")
            if len(previous_values) > detection_index:
                row["FECHA DE DETECCIÓN"] = previous_values[detection_index]
            values = [[row.get(column, "") for column in SHEET_COLUMNS]]
            self.sheets.spreadsheets().values().update(spreadsheetId=self.sheet_id, range=f"{worksheet}!A{match_row}", valueInputOption="RAW", body={"values": values}).execute()
        else:
            row["FECHA DE DETECCIÓN"] = now
            values = [[row.get(column, "") for column in SHEET_COLUMNS]]
            self.sheets.spreadsheets().values().append(spreadsheetId=self.sheet_id, range=f"{worksheet}!A:Z", valueInputOption="RAW", insertDataOption="INSERT_ROWS", body={"values": values}).execute()
