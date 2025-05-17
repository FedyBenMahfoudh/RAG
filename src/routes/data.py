from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request,File
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ConversationController, ProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schemes.data import ProcessRequest
from models import  ConversationModel,ChunkModel,AssetModel,CurrentUser
from models.db_schemes import DataChunk, Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
from typing import List,Optional
from models.db_schemes import Conversation
from guard.authGuard import guard

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
    dependencies=[Depends(guard)] 
)

@data_router.post("/upload")
async def upload_data(
    request: Request,
    files: List[UploadFile] = File(...),
    app_settings: Settings = Depends(get_settings),
    user: CurrentUser = Depends(guard)
):
    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )


    conversation = await conversation_model.create_conversation(
        Conversation(title="", user_id=user.id)
    )
    conversation_id = str(conversation.id)

    data_controller = DataController()
    files_id = []

    for file in files:
        is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": result_signal,
                    "file_error_id": file.filename
                }
            )

        conversation_dir_path = ConversationController().get_conversation_path(
            conversation_id=conversation_id,
            user_id=user.id
        )

        file_path, file_id = data_controller.generate_unique_filepath(
            orig_file_name=file.filename,
            conversation_id=conversation_id,
            user_id=user.id
        )

        try:
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                    await f.write(chunk)
        except Exception as e:
            logger.error(f"Error while uploading file: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": ResponseSignal.FILE_UPLOAD_FAILED.value}
            )

        asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )

        asset_resource = Asset(
            asset_conversation_id=conversation.id,
            asset_type=AssetTypeEnum.FILE.value,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path)
        )

        asset_record = await asset_model.create_asset(asset=asset_resource)
        files_id.append(str(asset_record.id))

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "files_id": files_id,
            "conversation_id": conversation_id
        }
    )

@data_router.post("/upload/{conversation_id}")
async def upload_to_existing_conversation(
    conversation_id: str,
    request: Request,
    files: List[UploadFile] = File(...),
    app_settings: Settings = Depends(get_settings),
    user: CurrentUser = Depends(guard)
):
    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )


    conversation = await conversation_model.get_conversation_or_create_one(
        conversation_id=conversation_id,
        user_id=user.id
    )   
    
    conversation_id = str(conversation.id)
    data_controller = DataController()
    files_id = []

    for file in files:
        is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": result_signal,
                    "file_error_id": file.filename
                }
            )

        conversation_dir_path = ConversationController().get_conversation_path(
            conversation_id=conversation_id,
            user_id=user.id
        )

        file_path, file_id = data_controller.generate_unique_filepath(
            orig_file_name=file.filename,
            conversation_id=conversation_id,
            user_id=user.id
        )

        try:
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                    await f.write(chunk)
        except Exception as e:
            logger.error(f"Error while uploading file: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": ResponseSignal.FILE_UPLOAD_FAILED.value}
            )

        asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )

        asset_resource = Asset(
            asset_conversation_id=conversation.id,
            asset_type=AssetTypeEnum.FILE.value,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path)
        )

        asset_record = await asset_model.create_asset(asset=asset_resource)
        files_id.append(str(asset_record.id))

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "files_id": files_id,
            "conversation_id": conversation_id
        }
    )



@data_router.post("/process/{conversation_id}")
async def process_endpoint(request: Request, conversation_id: str,process_request: ProcessRequest,user: CurrentUser = Depends(guard)):

    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )

    conversation = await conversation_model.get_conversation_or_create_one(
        conversation_id=conversation_id,
        user_id=user.id 
    )

    asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )

    conversation_files_ids = {}
    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_conversation_id=conversation.id,
            asset_name=process_request.file_id
        )

        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                }
            )

        conversation_files_ids = {
            asset_record.id: asset_record.asset_name
        }
    
    else:
        

        conversation_files = await asset_model.get_all_conversation_assets(
            asset_conversation_id=conversation.id,
            asset_type=AssetTypeEnum.FILE.value,
        )

        conversation_files_ids = {
            record.id: record.asset_name
            for record in conversation_files
        }

    if len(conversation_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value,
            }
        )
    
    process_controller = ProcessController(conversation_id=conversation_id,user_id=user.id)

    no_records = 0
    no_files = 0

    chunk_model = await ChunkModel.create_instance(
                        db_client=request.app.db_client
                    )

    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_conversation_id(
            conversation_id=conversation.id
        )

    for asset_id, file_id in conversation_files_ids.items():

        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            logger.error(f"Error while processing file: {file_id}")
            continue

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

        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i+1,
                chunk_conversation_id=conversation.id,
                chunk_asset_id=asset_id
            )
            for i, chunk in enumerate(file_chunks)
        ]

        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files
        }
    )
