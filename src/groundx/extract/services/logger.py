import logging, logging.config, typing

from .logging_cfg import logging_config


class Logger:
    def __init__(
        self,
        name: str,
        level: str,
    ) -> None:
        logging.config.dictConfig(logging_config(name, level))

        self.logger = logging.getLogger(name)

    def debug_msg(
        self,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
    ) -> None:
        self.print_msg("DEBUG", msg, name, document_id, task_id)

    def error_msg(
        self,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
    ) -> None:
        self.print_msg("ERROR", msg, name, document_id, task_id)

    def info_msg(
        self,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
    ) -> None:
        self.print_msg("INFO", msg, name, document_id, task_id)

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
    ) -> None:
        self.print_msg("WARNING", msg, name, document_id, task_id)

    def print_msg(
        self,
        level: str,
        msg: str,
        name: typing.Optional[str] = None,
        document_id: typing.Optional[str] = None,
        task_id: typing.Optional[str] = None,
    ) -> None:
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

        text = ""
        if prefix != "":
            text += f"{prefix} "
        text += f"\n\n\t>> {msg}\n"

        lvl = level.upper()
        if lvl == "ERROR":
            self.logger.error(text)
        elif lvl in ("WARN", "WARNING"):
            self.logger.warning(text)
        elif lvl == "INFO":
            self.logger.info(text)
        else:
            self.logger.debug(text)
