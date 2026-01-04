import inspect, json, logging, logging.config, typing

from .logging_cfg import logging_config


def caller_info() -> typing.Dict[str, typing.Any]:
    f = inspect.currentframe()
    c = inspect.getouterframes(f, 2)[1]
    return {
        "caller_function": c.function,
        "caller_file": c.filename,
        "caller_line": c.lineno,
    }


class Logger:
    def __init__(
        self,
        name: str,
        level: str,
        output: str = "json",
    ) -> None:
        logging.config.dictConfig(logging_config(name, level))

        self.logger = logging.getLogger(name)
        self.output = output.lower()

    def debug_msg(
        self,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
        extras: typing.Dict[str, typing.Any] = {},
    ) -> None:
        self.print_msg("DEBUG", msg, name, document_id, task_id, workflow_id, extras)

    def error_msg(
        self,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
        extras: typing.Dict[str, typing.Any] = {},
    ) -> None:
        self.print_msg("ERROR", msg, name, document_id, task_id, workflow_id, extras)

    def info_msg(
        self,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
        extras: typing.Dict[str, typing.Any] = {},
    ) -> None:
        self.print_msg("INFO", msg, name, document_id, task_id, workflow_id, extras)

    def report_error(
        self,
        api_key: str,
        callback_url: str,
        req: typing.Optional[typing.Dict[str, typing.Any]],
        msg: str,
    ) -> None:
        import requests

        self.error_msg(msg)

        if req is None or callback_url == "":
            return

        requests.post(
            callback_url,
            json=req,
            headers={"X-API-Key": api_key},
        )

    def report_result(
        self,
        api_key: str,
        callback_url: str,
        req: typing.Dict[str, typing.Any],
    ):
        import requests

        if callback_url == "":
            return

        self.info_msg("calling back to [%s]" % (callback_url))

        requests.post(
            callback_url,
            json=req,
            headers={"X-API-Key": api_key},
        )

    def warning_msg(
        self,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
        extras: typing.Dict[str, typing.Any] = {},
    ) -> None:
        self.print_msg("WARNING", msg, name, document_id, task_id, workflow_id, extras)

    def print_msg(
        self,
        level: str,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
        workflow_id: typing.Optional[str] = None,
        extras: typing.Dict[str, typing.Any] = {},
    ) -> None:
        logMsg: str = ""

        if self.output == "json":
            logDict: typing.Dict[str, typing.Any] = {
                "message": msg,
            }
            if name:
                logDict["file_name"] = name
            if document_id:
                logDict["document_id"] = document_id
            if task_id:
                logDict["task_id"] = task_id
            if workflow_id:
                logDict["workflow_id"] = workflow_id
            for k, v in extras.items():
                logDict[k] = v
            logMsg = json.dumps(logDict)
        else:
            logMsg = ""
            prefix = ""
            if name:
                if prefix != "":
                    prefix += " "
                prefix += f"[{name}]"
            if document_id:
                if prefix != "":
                    prefix += " "
                prefix += f"d [{document_id}]"
            if task_id:
                if prefix != "":
                    prefix += " "
                prefix += f"t [{task_id}]"
            if workflow_id:
                if prefix != "":
                    prefix += " "
                prefix += f"w [{workflow_id}]"

            ex = ""
            for k, v in extras.items():
                if ex != "":
                    ex += " "
                ex += f"{k} [{v}]"

            if ex != "":
                if prefix != "":
                    prefix += "\n"
                prefix += ex

            if prefix != "":
                logMsg += f"{prefix} "
            logMsg += f"\n\n\t>> {msg}\n"

        lvl = level.upper()
        if lvl == "ERROR":
            self.logger.error(logMsg)
        elif lvl in ("WARN", "WARNING"):
            self.logger.warning(logMsg)
        elif lvl == "INFO":
            self.logger.info(logMsg)
        else:
            self.logger.debug(logMsg)
