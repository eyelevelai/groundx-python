from ..classes.settings import ContainerSettings
from .logger import Logger


class Upload:
    def __init__(
        self,
        settings: ContainerSettings,
        logger: Logger,
    ):
        self.settings = settings
        self.logger = logger

        if self.settings.upload.type == "minio":
            from services.upload_minio import MinIOClient

            self.client = MinIOClient(self.settings, self.logger)
        elif self.settings.upload.type == "s3":
            from services.upload_s3 import S3Client

            self.client = S3Client(self.settings, self.logger)
        else:
            raise Exception(f"unsupported upload.type [{self.settings.upload.type}]")

    def get_file(self, url: str) -> bytes:
        return bytes()

    def get_object(self, url: str):
        self.client.get_object(url)

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ):
        self.client.put_object(bucket, key, data, content_type)

    def put_json_stream(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ):
        self.client.put_json_stream(bucket, key, data, content_type)
