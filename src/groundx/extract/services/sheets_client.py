import json
import os
import typing
from pathlib import Path

import gspread
from ..settings.settings import GCP_CREDENTIALS, ContainerSettings
from google.oauth2 import service_account
from googleapiclient.discovery import (
    build,  # pyright: ignore[reportUnknownVariableType]
)
from gspread.http_client import HTTPClient

SPREADSHEET_MIME = "application/vnd.google-apps.spreadsheet"
SHEETS_CONNECT_TIMEOUT_SECONDS = 5.0
SHEETS_READ_TIMEOUT_SECONDS = 30.0
DRIVE_SOCKET_TIMEOUT_SECONDS = 30.0


class _BoundedGspreadHTTPClient(HTTPClient):
    def __init__(self, auth: typing.Any, session: typing.Any = None) -> None:
        super().__init__(auth, session=session)
        self.timeout = (
            SHEETS_CONNECT_TIMEOUT_SECONDS,
            SHEETS_READ_TIMEOUT_SECONDS,
        )


class SheetsClient:
    client: gspread.Client
    # drive: DriveResource
    drive: typing.Any
    settings: ContainerSettings

    def __init__(
        self,
        settings: ContainerSettings,
        scopes: typing.Optional[typing.List[str]] = None,
    ):
        self.scopes: typing.List[str] = scopes or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        self.settings = settings

        creds_dict = _load_credentials_from_env()
        if not creds_dict:
            raise ValueError(f"{GCP_CREDENTIALS} does not load valid credentials")

        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scopes
        )
        import httplib2  # type: ignore[import-untyped]
        from google_auth_httplib2 import AuthorizedHttp  # type: ignore[import-untyped,import-not-found]

        drive_http = AuthorizedHttp(
            creds,
            http=httplib2.Http(timeout=DRIVE_SOCKET_TIMEOUT_SECONDS),
        )
        self.drive = build(
            "drive",
            "v3",
            http=drive_http,
            cache_discovery=False,
            num_retries=0,
            static_discovery=True,
        )

        auth_scopes = self.scopes
        if scopes:
            auth_scopes = scopes

        self.client = gspread.service_account_from_dict(
            creds_dict,
            scopes=auth_scopes,
            http_client=_BoundedGspreadHTTPClient,
        )

    def create_headers_if_missing(
        self, ws: gspread.Worksheet, headers: typing.List[str]
    ) -> None:
        existing = ws.row_values(1)
        if not existing:
            ws.insert_row(headers, 1)

    def find_sheet_by_name(
        self,
        spreadsheet_name: str,
        drive_id: str,
    ) -> typing.Optional[str]:
        cln = spreadsheet_name.replace("'", "\\'")

        q = f"name = '{cln}' and mimeType = '{SPREADSHEET_MIME}' and trashed = false"

        resp = (
            self.drive.files()
            .list(
                q=q,
                corpora="drive",
                driveId=drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="files(id, name)",
            )
            .execute(num_retries=0)
        )
        files = resp.get("files", [])
        return files[0].get("id") if files else None

    def open_or_create_spreadsheet(
        self,
        spreadsheet_name: str,
        drive_id: str,
        sheet_1_title: typing.Optional[str] = None,
    ) -> gspread.Spreadsheet:
        file_id = self.find_sheet_by_name(spreadsheet_name, drive_id)
        if file_id:
            return self.client.open_by_key(file_id)

        if self.settings.google_sheets_template_id:
            created = (
                self.drive.files()
                .copy(
                    fileId=self.settings.google_sheets_template_id,
                    body={"name": spreadsheet_name, "parents": [drive_id]},
                    supportsAllDrives=True,
                    fields="id,name,parents,driveId",
                )
                .execute(num_retries=0)
            )
        else:
            created = (
                self.drive.files()
                .create(
                    body={
                        "name": spreadsheet_name,
                        "mimeType": SPREADSHEET_MIME,
                        "parents": [drive_id],
                    },
                    supportsAllDrives=True,
                    fields="id,name,parents,driveId",
                )
                .execute(num_retries=0)
            )

        cid = created.get("id")
        if not cid:
            raise Exception(f"create spreadsheet failed\n{created}")

        sh = self.client.open_by_key(cid)

        if sheet_1_title:
            sh.sheet1.update_title(sheet_1_title)

        return sh

    def open_or_create_worksheet(
        self,
        sh: gspread.Spreadsheet,
        title: str,
        headers: typing.List[str],
        rows: int = 1000,
    ) -> gspread.Worksheet:
        cols = len(headers)
        try:
            ws = sh.worksheet(title)
            self.create_headers_if_missing(ws, headers)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=title, rows=rows, cols=cols)
            ws.append_row(headers)

        return ws


def _load_credentials_from_env() -> typing.Optional[typing.Dict[str, typing.Any]]:
    raw = os.environ.get(GCP_CREDENTIALS)
    if not raw:
        if Path("./gcv.json").exists():
            with open("./gcv.json") as f:
                data = f.read()
            return json.loads(data)

        return None

    try:
        creds = json.loads(raw)
        if not isinstance(creds, dict):
            raise ValueError(f"{GCP_CREDENTIALS} is not type dict [{type(creds)}]")

        return typing.cast(typing.Dict[str, typing.Any], creds)
    except Exception as e:
        raise ValueError(f"{GCP_CREDENTIALS} is set but not valid JSON: {e}") from e
