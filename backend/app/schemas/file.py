from pydantic import BaseModel


class FileUploadRequest(BaseModel):
    external_id: str
    filename: str


class BulkUploadRequest(BaseModel):
    files: list[FileUploadRequest]


class FileConfirmation(BaseModel):
    external_id: str
    file_size: int


class BulkConfirmUploadRequest(BaseModel):
    files: list[FileConfirmation]
