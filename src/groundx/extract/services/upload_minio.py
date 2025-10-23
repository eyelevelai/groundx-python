import typing

from .logger import Logger
from ..settings.settings import ContainerSettings


class MinIOClient:
    def __init__(
        self,
        settings: ContainerSettings,
        logger: Logger,
    ) -> None:
        self.settings = settings
        self.client = None
        self.logger = logger
        if self.settings.upload.type == "minio":
            import json
            from minio import Minio

            self.client = Minio(
                self.settings.upload.base_domain,
                access_key=self.settings.upload.get_key(),
                secret_key=self.settings.upload.get_secret(),
                region=self.settings.upload.get_region(),
                session_token=self.settings.upload.get_token(),
                secure=self.settings.upload.ssl,
            )

            if not self.client.bucket_exists(self.settings.upload.bucket):
                try:
                    self.client.make_bucket(self.settings.upload.bucket)
                    self.logger.info_msg(
                        f"Bucket '{self.settings.upload.bucket}' created."
                    )

                    self.client.set_bucket_policy(
                        self.settings.upload.bucket,
                        json.dumps(
                            {
                                "Version": "2012-10-17",
                                "Statement": [
                                    {
                                        "Effect": "Allow",
                                        "Principal": {"AWS": ["*"]},
                                        "Action": ["s3:GetObject"],
                                        "Resource": [
                                            f"arn:aws:s3:::{self.settings.upload.bucket}/*"
                                        ],
                                    }
                                ],
                            }
                        ),
                    )
                except Exception as e:
                    self.logger.warning_msg(str(e))
                    self.logger.warning_msg(
                        f"error creating bucket [{self.settings.upload.bucket}]"
                    )

    def get_object(self, url: str) -> typing.Optional[bytes]:
        if not self.client:
            return None

        from minio.error import S3Error

        try:
            minio_uri_parts = url.replace("s3://", "").split("/")
            bucket_name = minio_uri_parts[0]
            object_name = "/".join(minio_uri_parts[1:])

            response = self.client.get_object(bucket_name, object_name)

            return response.read()
        except S3Error as e:
            self.logger.error_msg(f"Failed to get object from {url}: {str(e)}")
            raise

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        if not self.client:
            return

        import io

        from minio.error import S3Error

        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            self.client.put_object(
                bucket_name=bucket,
                object_name=key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
        except S3Error as e:
            self.logger.error_msg(f"Failed to put object in {bucket}/{key}: {str(e)}")
            raise

    def put_json_stream(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        if not self.client:
            return

        self.put_object(
            bucket,
            key,
            data,
            content_type,
        )
