import os

import aiofiles
from fastapi import APIRouter,UploadFile,Depends,status
from fastapi.responses import JSONResponse
from models import ResponseSignal
from controllers import DataController, ProjectController
from helpers.config import Settings, get_settings
import logging

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
                "user" : user_id
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