"""S3-совместимое хранилище (AWS S3, MinIO, Cloudflare R2, Backblaze B2 и т.п.)."""

from __future__ import annotations

import asyncio
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.errors import StorageError
from app.services.storage.base import Storage


class S3Storage(Storage):
    def __init__(
        self,
        *,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,
        region: str = "us-east-1",
    ) -> None:
        self.bucket = bucket
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                connect_timeout=10,
                read_timeout=60,
                retries={"max_attempts": 5, "mode": "standard"},
                s3={"addressing_style": "path"},
            ),
        )

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"s3 put failed: {type(exc).__name__}") from exc

    async def get(self, key: str) -> bytes:
        try:
            response = await asyncio.to_thread(self._client.get_object, Bucket=self.bucket, Key=key)
            body = response["Body"]
            try:
                return await asyncio.to_thread(body.read)
            finally:
                body.close()
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"s3 get failed: {type(exc).__name__}") from exc

    async def exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(self._client.head_object, Bucket=self.bucket, Key=key)
        except ClientError:
            return False
        return True

    async def delete(self, key: str) -> None:
        try:
            await asyncio.to_thread(self._client.delete_object, Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"s3 delete failed: {type(exc).__name__}") from exc

    async def ensure_bucket(self) -> None:
        try:
            await asyncio.to_thread(self._client.head_bucket, Bucket=self.bucket)
            return
        except ClientError:
            pass
        try:
            await asyncio.to_thread(self._client.create_bucket, Bucket=self.bucket)
        except ClientError as exc:
            # Бакет мог создать параллельно стартующий сервис (bot / worker).
            code = exc.response.get("Error", {}).get("Code", "")
            if code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                raise StorageError(f"cannot create bucket: {code}") from exc

    async def ensure_ready(self) -> None:
        await self.ensure_bucket()

    async def healthcheck(self) -> bool:
        try:
            await asyncio.to_thread(self._client.head_bucket, Bucket=self.bucket)
        except (BotoCoreError, ClientError):
            return False
        return True
