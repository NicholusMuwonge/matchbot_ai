from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    MINIO_ENDPOINT: str = Field(
        default="minio:9000",
        description="MinIO server endpoint (host:port) for backend connections",
    )
    MINIO_EXTERNAL_ENDPOINT: str | None = Field(
        default=None,
        description="MinIO external endpoint (host:port) for client-facing presigned URLs. If not set, uses MINIO_ENDPOINT",
    )
    MINIO_ACCESS_KEY: str = Field(
        default="minioadmin",
        description="MinIO access key for authentication",
    )
    MINIO_SECRET_KEY: str = Field(
        default="minioadmin",
        description="MinIO secret key for authentication",
    )
    MINIO_SECURE: bool = Field(
        default=False,
        description="Use HTTPS for MinIO connections (False for development)",
    )
    MINIO_REGION: str = Field(
        default="us-east-1",
        description="MinIO region configuration",
    )

    MINIO_BUCKET_RECONCILIATION: str = Field(
        default="reconciliation-files",
        description="Bucket name for reconciliation files",
    )
    MINIO_BUCKET_REPORTS: str = Field(
        default="reconciliation-reports",
        description="Bucket name for generated reports",
    )
    MINIO_BUCKET_TEMP: str = Field(
        default="temp-uploads",
        description="Bucket name for temporary uploads",
    )

    RECONCILIATION_FILES_PREFIX: str = Field(
        default="reconciliations",
        description="Path prefix for reconciliation files (e.g., 'reconciliations')",
    )
    RECONCILIATION_RESULTS_PREFIX: str = Field(
        default="reconciliations_results",
        description="Path prefix for reconciliation results (e.g., 'reconciliations_results')",
    )

    UPLOAD_MAX_FILE_SIZE: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximum file size in bytes for uploads",
    )
    UPLOAD_ALLOWED_EXTENSIONS: list[str] = Field(
        default=[".csv", ".xlsx", ".xls"],
        description="Allowed file extensions for upload",
    )
    UPLOAD_PRESIGNED_URL_EXPIRY: int = Field(
        default=3600,  # 1 hour
        description="Presigned URL expiration time in seconds for uploads",
    )
    DOWNLOAD_PRESIGNED_URL_EXPIRY: int = Field(
        default=7200,  # 2 hours
        description="Presigned URL expiration time in seconds for downloads",
    )

    UNCONFIRMED_FILE_TTL_HOURS: int = Field(
        default=24,
        description="Hours before unconfirmed files are deleted",
    )
    COMPLETED_FILE_ARCHIVE_DAYS: int = Field(
        default=30,
        description="Days before completed reconciliation files are archived",
    )
    TEMP_FILE_TTL_HOURS: int = Field(
        default=1,
        description="Hours before temporary files are purged",
    )

    MINIO_CONNECTION_POOL_SIZE: int = Field(
        default=10,
        description="Maximum number of MinIO connections in pool",
    )
    MINIO_CONNECTION_TIMEOUT: int = Field(
        default=30,
        description="Connection timeout in seconds",
    )

    MINIO_MAX_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="Maximum number of retry attempts for MinIO operations",
    )
    MINIO_RETRY_INITIAL_DELAY: float = Field(
        default=1.0,
        description="Initial delay in seconds for retry backoff",
    )
    MINIO_RETRY_MAX_DELAY: float = Field(
        default=30.0,
        description="Maximum delay in seconds for retry backoff",
    )

    @property
    def allowed_content_types(self) -> dict[str, str]:
        return {
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
        }

    def is_file_allowed(self, filename: str) -> bool:
        import os

        ext = os.path.splitext(filename)[1].lower()
        return ext in self.UPLOAD_ALLOWED_EXTENSIONS

    def get_content_type(self, filename: str) -> str | None:
        import os

        ext = os.path.splitext(filename)[1].lower()
        return self.allowed_content_types.get(ext)

    @property
    def minio_url(self) -> str:
        """Internal MinIO URL for backend connections"""
        protocol = "https" if self.MINIO_SECURE else "http"
        return f"{protocol}://{self.MINIO_ENDPOINT}"

    @property
    def minio_external_url(self) -> str:
        """External MinIO URL for client-facing presigned URLs"""
        protocol = "https" if self.MINIO_SECURE else "http"
        endpoint = self.MINIO_EXTERNAL_ENDPOINT or self.MINIO_ENDPOINT
        return f"{protocol}://{endpoint}"

    @property
    def required_buckets(self) -> list[str]:
        return [
            self.MINIO_BUCKET_RECONCILIATION,
            self.MINIO_BUCKET_REPORTS,
            self.MINIO_BUCKET_TEMP,
        ]


storage_config = StorageConfig()
