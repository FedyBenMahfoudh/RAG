from fastapi import UploadFile
from pydantic import BaseModel
from typing import Optional,List

class UploadRequest(BaseModel):
    files : List[UploadFile]
    user_id : str


class ProcessRequest(BaseModel):
    file_id: str = None
    chunk_size: Optional[int] = 100
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0
