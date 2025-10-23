import json, os, shutil, requests, time, typing
from datetime import datetime, timezone
from io import BytesIO
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from .groundx import GroundXDocument
from ..services.logger import Logger
from ..utility.classes import clean_json


DocT = typing.TypeVar("DocT", bound="Document")


class Document(BaseModel):
    file_name: str = ""

    document_id: str = ""
    page_images: typing.List[str] = []
    source_url: str = ""
    task_id: str = ""

    _logger: typing.Optional[Logger] = PrivateAttr(default=None)

    @property
    def logger(self) -> typing.Optional[Logger]:
        if self._logger:
            return self._logger

        return None

    @logger.setter
    def logger(self, value: Logger) -> None:
        self._logger = value

    @logger.deleter
    def logger(self) -> None:
        del self._logger

    @classmethod
    def from_request(
        cls: typing.Type[DocT],
        base_url: str,
        req: "DocumentRequest",
        **data: typing.Any,
    ) -> DocT:
        st = cls(**data)

        st.document_id = req.document_id
        st.file_name = req.file_name
        st.task_id = req.task_id

        xray_doc = GroundXDocument(
            base_url=base_url,
            documentID=req.document_id,
            taskID=req.task_id,
        ).xray(clear_cache=req.clear_cache)

        for page in xray_doc.documentPages:
            st.page_images.append(page.pageUrl)

        st.source_url = xray_doc.sourceUrl

        for chunk in xray_doc.chunks:
            stxt = chunk.sectionSummary or "{}"
            stxt = clean_json(stxt)
            try:
                data = json.loads(stxt)
            except json.JSONDecodeError:
                st.print("ERROR", f"\njson.JSONDecodeError stxt\n{stxt}\n\n")
                continue

            for key, value in data.items():
                err = st.add(key, value)
                if err:
                    raise Exception(f"\n\ninit document error:\n\t{err}\n")

            mtxt = chunk.suggestedText or "{}"
            mtxt = clean_json(mtxt)
            try:
                data = json.loads(mtxt)
            except json.JSONDecodeError:
                st.print("ERROR", f"\njson.JSONDecodeError mtxt\n{mtxt}\n\n")
                continue

            for key, value in data.items():
                err = st.add(key, value)
                if err:
                    raise Exception(f"\n\ninit document error:\n\t{err}\n")

        st.finalize_init()

        return st

    def add(self, k: str, value: typing.Any) -> typing.Union[str, None]:
        self.print("WARNING", "add is not implemented")

        return None

    def finalize_init(self) -> None:
        self.print("WARNING", "finalize_init is not implemented")

    def print(self, level: str, msg: str) -> None:
        if not self.logger:
            print(msg)
            return

        lvl = level.upper()
        if lvl == "ERROR":
            self.logger.error_msg(msg, self.file_name, self.document_id, self.task_id)
        elif lvl == "INFO":
            self.logger.info_msg(msg, self.file_name, self.document_id, self.task_id)
        elif lvl in ("WARN", "WARNING"):
            self.logger.warning_msg(msg, self.file_name, self.document_id, self.task_id)
        else:
            self.logger.debug_msg(msg, self.file_name, self.document_id, self.task_id)


def _new_page_image_dict() -> typing.Dict[str, int]:
    return {}


def _new_page_images() -> typing.List[Image.Image]:
    return []


class DocumentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    callback_url: str = Field(alias="callbackURL", default="")
    document_id: str = Field(alias="documentID")
    file_name: str = Field(alias="fileName")
    model_id: int = Field(alias="modelID")
    processor_id: int = Field(alias="processorID")
    task_id: str = Field(alias="taskID")

    _logger: typing.Optional[Logger] = PrivateAttr(default=None)

    _append_values: bool = PrivateAttr(default_factory=bool)
    _clear_cache: bool = PrivateAttr(default_factory=bool)
    _debug_path: typing.Optional[str] = PrivateAttr(default=None)
    _page_image_dict: typing.Dict[str, int] = PrivateAttr(
        default_factory=_new_page_image_dict
    )
    _page_images: typing.List[Image.Image] = PrivateAttr(
        default_factory=_new_page_images
    )
    _start: int = PrivateAttr(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp())
    )
    _write_lock: typing.Optional[typing.Any] = PrivateAttr(default=None)

    @property
    def append_values(self) -> bool:
        return self._append_values

    @append_values.setter
    def append_values(self, value: bool) -> None:
        self._append_values = value

    @append_values.deleter
    def append_values(self) -> None:
        del self._append_values

    @property
    def clear_cache(self) -> bool:
        return self._clear_cache

    @clear_cache.setter
    def clear_cache(self, value: bool) -> None:
        self._clear_cache = value

    @clear_cache.deleter
    def clear_cache(self) -> None:
        del self._clear_cache

    @property
    def debug_path(self) -> typing.Optional[str]:
        return self._debug_path

    @debug_path.setter
    def debug_path(self, value: str) -> None:
        self._debug_path = value

    @debug_path.deleter
    def debug_path(self) -> None:
        del self._debug_path

    @property
    def logger(self) -> typing.Optional[Logger]:
        if self._logger:
            return self._logger

        return None

    @logger.setter
    def logger(self, value: Logger) -> None:
        self._logger = value

    @logger.deleter
    def logger(self) -> None:
        del self._logger

    @property
    def page_images(self) -> typing.List[Image.Image]:
        return self._page_images

    @page_images.setter
    def page_images(self, value: typing.List[Image.Image]) -> None:
        self._page_images = value

    @page_images.deleter
    def page_images(self) -> None:
        del self._page_images

    @property
    def page_image_dict(self) -> typing.Dict[str, int]:
        return self._page_image_dict

    @page_image_dict.setter
    def page_image_dict(self, value: typing.Dict[str, int]) -> None:
        self._page_image_dict = value

    @page_image_dict.deleter
    def page_image_dict(self) -> None:
        del self._page_image_dict

    @property
    def start(self) -> int:
        return self._start

    @property
    def write_lock(self) -> typing.Optional[typing.Any]:
        return self._write_lock

    @write_lock.setter
    def write_lock(self, value: typing.Optional[typing.Any]) -> None:
        self._write_lock = value

    @write_lock.deleter
    def write_lock(self) -> None:
        del self._write_lock

    def clear_debug(self) -> None:
        if self.debug_path:
            file_path = f"{self.debug_path}/{self.file_name.replace('.pdf','')}"
            shutil.rmtree(file_path, ignore_errors=True)

    def load_images(
        self,
        imgs: typing.List[str],
        attempt: int = 0,
        should_sleep: bool = True,
    ) -> typing.List[Image.Image]:
        pageImages: typing.List[Image.Image] = []
        for page in imgs:
            if page in self.page_image_dict:
                self.print(
                    "WARN",
                    f"[{attempt}] loading cached [{self.page_image_dict[page]}] [{page}]",
                )
                pageImages.append(self.page_images[self.page_image_dict[page]])
            else:
                try:
                    self.print("WARN", f"[{attempt}] downloading [{page}]")
                    resp = requests.get(page)
                    resp.raise_for_status()
                    img = Image.open(BytesIO(resp.content))
                    if img:
                        self.page_image_dict[page] = len(self.page_images)
                        self.page_images.append(img)
                        pageImages.append(img)
                except Exception as e:
                    self.print(
                        "ERROR", f"[{attempt}] Failed to load image from {page}: {e}"
                    )
                    if attempt < 2:
                        if should_sleep:
                            time.sleep(2 * attempt + 1)
                        return self.load_images(
                            imgs, attempt + 1, should_sleep=should_sleep
                        )

        return pageImages

    def print(self, level: str, msg: str) -> None:
        if not self.logger:
            print(msg)
            return

        lvl = level.upper()
        if lvl == "ERROR":
            self.logger.error_msg(msg, self.file_name, self.document_id, self.task_id)
        elif lvl == "INFO":
            self.logger.info_msg(msg, self.file_name, self.document_id, self.task_id)
        elif lvl in ("WARN", "WARNING"):
            self.logger.warning_msg(msg, self.file_name, self.document_id, self.task_id)
        else:
            self.logger.debug_msg(msg, self.file_name, self.document_id, self.task_id)

    def write_debug(self, file_name: str, data: typing.Any) -> None:
        if not self.debug_path:
            return

        os.makedirs(self.debug_path, exist_ok=True)
        file_path = f"{self.debug_path}/{self.file_name.replace('.pdf','')}"
        os.makedirs(file_path, exist_ok=True)

        if not isinstance(data, str):
            try:
                data = json.dumps(data)
            except Exception as e:
                if isinstance(data, Exception):
                    data = str(data)
                else:
                    self.print("ERROR", f"write_debug exception: {e}")
                    raise e

        with open(f"{file_path}/{self.start}_{file_name}", "w", encoding="utf-8") as f:
            f.write(data)
