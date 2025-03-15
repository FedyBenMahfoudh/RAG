import os

import aiofiles
from fastapi import APIRouter,UploadFile,Depends,status
from fastapi.responses import JSONResponse
from models import ResponseSignal
from controllers import DataController, ProjectController, ProcessController
from helpers.config import Settings, get_settings
import logging
from .schemes.data import ProcessRequest
logger = logging.getLogger('uvicorn.error')


data_router = APIRouter(prefix="/model/v1/data",tags=["data","model-v1"])

@data_router.post("/upload/{user_id}")
async def upload_file(user_id : str,file: UploadFile,app_settings: Settings = Depends(get_settings),):
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal,
            }
        )

    user_dir_path = ProjectController().get_project_path(user_id=user_id)
    file_path = os.path.join(user_dir_path,file.filename)
    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )


    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value ,
        }
    )

@data_router.post("/process/{user_id}")
async def process_file(user_id: str,process_request:ProcessRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    process_controller = ProcessController(user_id=user_id)

    file_content = process_controller.get_file_content(file_id=file_id)

    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value
            }
        )

    return file_chunks