from fastapi import APIRouter,UploadFile,Depends,status
from fastapi.responses import JSONResponse

from controllers import DataController
from helpers.config import Settings, get_settings

data_router = APIRouter(prefix="/model/v1/data",tags=["model-v1","data"])

@data_router.post("/upload")
async def upload_file(file: UploadFile,app_settings: Settings = Depends(get_settings)):
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )

@data_router.get("/get-data")
async def getdata():
    return {"data": "Hello World"}