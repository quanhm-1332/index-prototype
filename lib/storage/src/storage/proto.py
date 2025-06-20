from typing import Protocol, BinaryIO
from dataclasses import dataclass


@dataclass(slots=True)
class ObjectStorageOptionalGetArgs:
    pass


@dataclass(slots=True)
class ObjectStorageOptionalPutArgs:
    pass


class ObjectStorage(Protocol):

    async def get_file(
        self,
        bucket_name: str,
        object_name: str,
        optional_args: ObjectStorageOptionalGetArgs = ObjectStorageOptionalGetArgs(),
    ) -> bytes | None: ...

    async def put_file(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        optional_args: ObjectStorageOptionalPutArgs = ObjectStorageOptionalPutArgs(),
    ) -> tuple[str, str] | None: ...
