import json, requests, typing
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated

from ..services.upload import Upload


class GroundXDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    base_url: str
    document_id: str = Field(alias="documentID")
    task_id: str = Field(alias="taskID")

    def xray_path(self) -> str:
        return f"layout/processed/{self.task_id}/{self.document_id}-xray.json"

    def xray_url(self, base: typing.Optional[str] = None) -> str:
        if not base:
            base = self.base_url
        if base.endswith("/"):
            base = base[:-1]
        return f"{base}/layout/processed/{self.task_id}/{self.document_id}-xray.json"

    def xray(
        self,
        cache_dir: Path,
        upload: typing.Optional[Upload] = None,
        clear_cache: bool = False,
        is_test: bool = False,
        base: typing.Optional[str] = None,
    ) -> "XRayDocument":
        return XRayDocument.download(
            self,
            cache_dir=cache_dir,
            upload=upload,
            clear_cache=clear_cache,
            is_test=is_test,
            base=base,
        )


class GroundXResponse(BaseModel):
    code: int
    document_id: str = Field(alias="documentID")
    model_id: int = Field(alias="modelID")
    processor_id: int = Field(alias="processorID")
    result_url: str = Field(alias="resultURL")
    task_id: str = Field(alias="taskID")


class BoundingBox(BaseModel):
    bottomRightX: float
    bottomRightY: float
    topLeftX: float
    topLeftY: float
    corrected: typing.Optional[bool]
    pageNumber: typing.Optional[int]


class Chunk(BaseModel):
    boundingBoxes: Annotated[typing.List[BoundingBox], Field(default_factory=list)]
    chunk: typing.Optional[str] = None
    chunkKeywords: typing.Optional[str] = None
    contentType: Annotated[typing.List[str], Field(default_factory=list)]
    fileKeywords: typing.Optional[str] = None
    fileSummary: typing.Optional[str] = None
    json_: typing.Optional[typing.List[typing.Any]] = Field(None, alias="json")
    multimodalUrl: typing.Optional[str] = None
    narrative: typing.Optional[typing.List[str]] = None
    pageNumbers: Annotated[typing.List[int], Field(default_factory=list)]
    sectionKeywords: typing.Optional[str] = None
    sectionSummary: typing.Optional[str] = None
    suggestedText: typing.Optional[str] = None
    text: typing.Optional[str] = None

    def get_extract(self) -> typing.Dict[str, typing.Any]:
        chunk_dict = self.model_dump(exclude_none=True)

        if "boundingBoxes" in chunk_dict:
            chunk_dict.pop("boundingBoxes")
        if "json_" in chunk_dict:
            chunk_dict.pop("json_")
        if "narrative" in chunk_dict:
            chunk_dict.pop("narrative")
        if "text" in chunk_dict:
            chunk_dict.pop("text")

        return chunk_dict


class DocumentPage(BaseModel):
    chunks: typing.List[Chunk]
    height: float
    pageNumber: int
    pageUrl: str
    width: float

    def get_extract(self) -> typing.Dict[str, typing.Any]:
        page_dict = self.model_dump(exclude_none=True)

        if "chunks" in page_dict:
            page_dict.pop("chunks")

        return page_dict


class XRayDocument(BaseModel):
    chunks: typing.List[Chunk]
    documentPages: Annotated[typing.List[DocumentPage], Field(default_factory=list)]
    sourceUrl: str
    fileKeywords: typing.Optional[str] = None
    fileName: typing.Optional[str] = None
    fileType: typing.Optional[str] = None
    fileSummary: typing.Optional[str] = None
    language: typing.Optional[str] = None

    @classmethod
    def download(
        cls,
        gx_doc: GroundXDocument,
        cache_dir: Path,
        upload: typing.Optional[Upload] = None,
        clear_cache: bool = False,
        is_test: bool = False,
        base: typing.Optional[str] = None,
    ) -> "XRayDocument":
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{gx_doc.document_id}-xray.json"

        if not clear_cache and cache_file.exists():
            try:
                with cache_file.open("r", encoding="utf-8") as f:
                    payload = json.load(f)

                return cls(**payload)
            except Exception as e:
                raise RuntimeError(
                    f"Error loading cached X-ray JSON from {cache_file}: {e}"
                )

        if upload:
            path = gx_doc.xray_path()
            ru = upload.get_object(path)
            if ru:
                try:
                    payload = json.loads(ru.decode("utf-8"))
                    return cls(**payload)
                except Exception as e:
                    raise RuntimeError(
                        f"Error decoding X-ray JSON bytes from {path}: {e}"
                    )

        url = gx_doc.xray_url(base=base)
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Error fetching X-ray JSON from {url}: {e}")

        try:
            payload = resp.json()
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON returned from {url}: {e}")

        if is_test is False:
            try:
                with cache_file.open("w", encoding="utf-8") as f:
                    json.dump(payload, f)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to write X-ray JSON cache to {cache_file}: {e}"
                )

        return cls(**payload)

    def get_extract(self) -> typing.Dict[str, typing.Any]:
        xray_dict = self.model_dump(exclude_none=True)

        chunks_list: typing.List[typing.Dict[str, typing.Any]] = []
        for c in self.chunks:
            chunks_list.append(c.get_extract())
        xray_dict["chunks"] = chunks_list

        pages_list: typing.List[typing.Dict[str, typing.Any]] = []
        for p in self.documentPages:
            pages_list.append(p.get_extract())
        xray_dict["documentPages"] = pages_list

        return xray_dict
