from dataclasses import asdict
from typing import BinaryIO

import logfire

import minio
from minio.sse import SseCustomerKey, Sse
from minio.commonconfig import Tags
from minio.retention import Retention

from structlog.stdlib import BoundLogger

from settings import MinioSettings

from logs import get_logger

from .proto import (
    ObjectStorage,
    ObjectStorageOptionalGetArgs,
    ObjectStorageOptionalPutArgs,
)


class MinIOOptionalGetArgs(ObjectStorageOptionalGetArgs):
    offset: int = 0
    length: int = 0
    request_headers: dict[str, str | list[str] | tuple[str]] | None = None
    ssec: SseCustomerKey | None = None
    version_id: str | None = None
    extra_query_params: dict[str, str | list[str] | tuple[str]] | None = None


class MinIOOptionalPutArgs(ObjectStorageOptionalPutArgs):
    length: int = 1
    content_type: str = "application/octet-stream"
    metadata: dict[str, str | list[str] | tuple[str]] | None = None
    sse: Sse | None = None
    part_size: int = 0
    num_parallel_uploads: int = 3
    tags: Tags | None = None
    retention: Retention | None = None
    legal_hold: bool = False


class MinIOStorage(ObjectStorage):
    def __init__(
        self, settings: MinioSettings, logger: BoundLogger = get_logger("S3.MinIO")
    ):
        self._client = minio.Minio(
            endpoint=settings.endpoint,
            access_key=settings.access_key.get_secret_value(),
            secret_key=settings.secret_key.get_secret_value(),
            secure=False,
        )
        self._logger = logger

    async def _check_bucket(self, bucket_name: str):
        if not self._client.bucket_exists(bucket_name):
            await self._logger.ainfo(
                "Bucket do not exists, creating new one", bucket_name=bucket_name
            )
            self._client.make_bucket(bucket_name)

    @logfire.instrument("MinIO get file: {bucket_name=} - {object_name=}")
    async def get_file(
        self,
        bucket_name: str,
        object_name: str,
        optional_args: ObjectStorageOptionalGetArgs = ObjectStorageOptionalGetArgs(),
    ) -> bytes | None:
        kwargs = {}
        if isinstance(optional_args, MinIOOptionalGetArgs):
            kwargs = asdict(optional_args)
        resp = None
        try:
            resp = self._client.get_object(bucket_name, object_name, **kwargs)
            if resp.status == 200:
                await self._logger.ainfo(
                    "File found", bucket_name=bucket_name, object_name=object_name
                )
                return resp.read()
            await self._logger.ainfo(
                "File not found", bucket_name=bucket_name, object_name=object_name
            )
            return None
        except Exception:
            await self._logger.aexception(
                "Error getting file", bucket_name=bucket_name, object_name=object_name
            )
            return None
        finally:
            if resp:
                resp.close()
                resp.release_conn()

    async def put_file(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        optional_args: ObjectStorageOptionalPutArgs = ObjectStorageOptionalPutArgs(),
    ) -> tuple[str, str] | None:
        try:
            await self._check_bucket(bucket_name)
            kwargs = {}
            if isinstance(optional_args, MinIOOptionalPutArgs):
                kwargs = asdict(optional_args)
            data_length = len(data.read())
            data.seek(0)
            _ = self._client.put_object(
                bucket_name, object_name, data, length=data_length, **kwargs
            )
            await self._logger.ainfo(
                "File uploaded", bucket_name=bucket_name, object_name=object_name
            )
            return (bucket_name, object_name)
        except Exception:
            await self._logger.aexception(
                "Error uploading file", bucket_name=bucket_name, object_name=object_name
            )
            return None
