from app.core.config import Settings
from app.services.storage.base import Storage, build_object_key
from app.services.storage.local import LocalStorage


def create_storage(settings: Settings) -> Storage:
    if settings.storage_backend == "s3":
        from app.services.storage.s3 import S3Storage

        return S3Storage(
            bucket=settings.s3_bucket,
            access_key=settings.s3_access_key.get_secret_value(),
            secret_key=settings.s3_secret_key.get_secret_value(),
            endpoint_url=settings.s3_endpoint_url,
            region=settings.s3_region,
        )
    return LocalStorage(settings.local_storage_path)


__all__ = ["LocalStorage", "Storage", "build_object_key", "create_storage"]
