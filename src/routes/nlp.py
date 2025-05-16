from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest, SearchRequest
from models.ConversationModel import ConversationModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models import ResponseSignal

import logging

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{user_id}/{conversation_id}")
async def index_conversation(request: Request, conversation_id: str,user_id:str, push_request: PushRequest):

    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    conversation = await conversation_model.get_conversation_or_create_one(
        conversation_id=conversation_id,
        user_id=user_id  
    )

    if not conversation:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.CONVERSATION_NOT_FOUND_ERROR.value
            }
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    has_records = True
    page_no = 1
    inserted_items_count = 0
    idx = 0

    while has_records:
        page_chunks = await chunk_model.get_conversation_chunks(conversation_id=conversation.id, page_no=page_no)
        if len(page_chunks):
            page_no += 1
        
        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break

        chunks_ids =  list(range(idx, idx + len(page_chunks)))
        idx += len(page_chunks)
        
        is_inserted = nlp_controller.index_into_vector_db(
            conversation=conversation,
            chunks=page_chunks,
            do_reset=push_request.do_reset,
            chunks_ids=chunks_ids
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value
                }
            )
        
        inserted_items_count += len(page_chunks)
        
    return JSONResponse(
        content={
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_items_count": inserted_items_count
        }
    )

@nlp_router.get("/index/info/{user_id}/{conversation_id}")
async def get_conversation_index_info(request: Request,user_id:str, conversation_id: str):
    
    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )

    conversation = await conversation_model.get_conversation_or_create_one(
        conversation_id=conversation_id,
        user_id=user_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    collection_info = nlp_controller.get_vector_db_collection_info(conversation=conversation)

    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info
        }
    )

@nlp_router.post("/index/search/{user_id}/{conversation_id}")
async def search_index(request: Request, conversation_id: str,user_id:str, search_request: SearchRequest):
    
    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )

    conversation = await conversation_model.get_conversation_or_create_one(
        conversation_id=conversation_id,
        user_id=user_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    results = nlp_controller.search_vector_db_collection(
        conversation=conversation, text=search_request.text, limit=search_request.limit
    )

    if not results:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value
                }
            )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "results": [ result.dict()  for result in results ]
        }
    )

@nlp_router.post("/index/answer/{user_id}/{conversation_id}")
async def answer_rag(request: Request, conversation_id: str,user_id:str, search_request: SearchRequest):
    
    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )

    conversation = await conversation_model.get_conversation_or_create_one(
        conversation_id=conversation_id,
        user_id=user_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    answer, full_prompt, chat_history = nlp_controller.answer_rag_question(
        conversation=conversation,
        query=search_request.text,
        limit=search_request.limit,
    )

    if not answer:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.RAG_ANSWER_ERROR.value
                }
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }
    )
