import sys
import types
import typing
from unittest.mock import Mock, patch

from groundx.extract.services.sheets_client import SheetsClient


def _settings(template_id: typing.Optional[str] = None) -> typing.Any:
    return types.SimpleNamespace(google_sheets_template_id=template_id)


def test_sheets_client_builds_bounded_no_retry_transports() -> None:
    creds = Mock()
    raw_http = Mock()
    authorized_http = Mock()
    http_factory = Mock(return_value=raw_http)
    authorized_http_factory = Mock(return_value=authorized_http)
    httplib2_module = types.ModuleType("httplib2")
    setattr(httplib2_module, "Http", http_factory)
    google_auth_httplib2_module = types.ModuleType("google_auth_httplib2")
    setattr(google_auth_httplib2_module, "AuthorizedHttp", authorized_http_factory)

    with (
        patch.dict(
            sys.modules,
            {
                "google_auth_httplib2": google_auth_httplib2_module,
                "httplib2": httplib2_module,
            },
        ),
        patch(
            "groundx.extract.services.sheets_client._load_credentials_from_env",
            return_value={"type": "service_account"},
        ),
        patch(
            "groundx.extract.services.sheets_client.service_account.Credentials.from_service_account_info",
            return_value=creds,
        ),
        patch("groundx.extract.services.sheets_client.build") as build,
        patch(
            "groundx.extract.services.sheets_client.gspread.service_account_from_dict"
        ) as service_account_from_dict,
    ):
        SheetsClient(_settings())

    http_factory.assert_called_once_with(timeout=30.0)
    authorized_http_factory.assert_called_once_with(creds, http=raw_http)
    build.assert_called_once_with(
        "drive",
        "v3",
        http=authorized_http,
        cache_discovery=False,
        num_retries=0,
        static_discovery=True,
    )
    bounded_http_client = service_account_from_dict.call_args.kwargs["http_client"]
    with patch("gspread.http_client.HTTPClient.__init__", return_value=None):
        client = bounded_http_client(Mock())
    assert client.timeout == (5.0, 30.0)


def test_drive_list_disables_generated_retries() -> None:
    request = Mock()
    request.execute.return_value = {"files": []}
    files = Mock()
    files.list.return_value = request
    drive = Mock()
    drive.files.return_value = files
    client = object.__new__(SheetsClient)
    client.drive = drive

    assert client.find_sheet_by_name("sheet", "drive-1") is None

    request.execute.assert_called_once_with(num_retries=0)


def test_drive_create_and_copy_disable_generated_retries() -> None:
    for template_id, method_name in ((None, "create"), ("template-1", "copy")):
        request = Mock()
        request.execute.return_value = {"id": "sheet-1"}
        files = Mock()
        getattr(files, method_name).return_value = request
        drive = Mock()
        drive.files.return_value = files
        client = object.__new__(SheetsClient)
        client.settings = _settings(template_id)
        client.drive = drive
        client.client = Mock()
        client.find_sheet_by_name = Mock(return_value=None)  # type: ignore[method-assign]

        client.open_or_create_spreadsheet("sheet", "drive-1")

        request.execute.assert_called_once_with(num_retries=0)
