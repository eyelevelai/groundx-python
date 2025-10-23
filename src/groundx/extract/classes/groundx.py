import json, requests, typing
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class GroundXDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    base_url: str
    document_id: str = Field(alias="documentID")
    task_id: str = Field(alias="taskID")

    def xray_url(self, base: typing.Optional[str] = None) -> str:
        if not base:
            base = self.base_url
        if base.endswith("/"):
            base = base[:-1]
        return f"{base}/layout/processed/{self.task_id}/{self.document_id}-xray.json"

    def xray(
        self,
        clear_cache: bool = False,
        is_test: bool = False,
        base: typing.Optional[str] = None,
    ) -> "XRayDocument":
        return XRayDocument.download(
            self, base=base, clear_cache=clear_cache, is_test=is_test
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
    boundingBoxes: typing.Optional[typing.List[BoundingBox]] = []
    chunk: typing.Optional[str] = None
    contentType: typing.Optional[typing.List[str]] = []
    json_: typing.Optional[typing.List[typing.Any]] = Field(None, alias="json")
    multimodalUrl: typing.Optional[str] = None
    narrative: typing.Optional[typing.List[str]] = None
    pageNumbers: typing.Optional[typing.List[int]] = []
    sectionSummary: typing.Optional[str] = None
    suggestedText: typing.Optional[str] = None
    text: typing.Optional[str] = None


class DocumentPage(BaseModel):
    chunks: typing.List[Chunk]
    height: float
    pageNumber: int
    pageUrl: str
    width: float


class XRayDocument(BaseModel):
    chunks: typing.List[Chunk]
    documentPages: typing.List[DocumentPage] = []
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
        clear_cache: bool = False,
        is_test: bool = False,
        base: typing.Optional[str] = None,
    ) -> "XRayDocument":
        cache_dir = Path(__file__).resolve().parent.parent / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{gx_doc.document_id}-xray.json"

        if not clear_cache and cache_file.exists():
            try:
                with cache_file.open("r", encoding="utf-8") as f:
                    payload = json.load(f)

            except Exception as e:
                raise RuntimeError(
                    f"Error loading cached X-ray JSON from {cache_file}: {e}"
                )
        else:
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
                    print(
                        f"Warning: failed to write X-ray JSON cache to {cache_file}: {e}"
                    )

        return cls(**payload)
