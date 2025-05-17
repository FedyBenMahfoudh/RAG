from .BaseDataModel import BaseDataModel
from .db_schemes import Conversation
from .enums.DataBaseEnum import DataBaseEnum
import datetime
from bson.objectid import ObjectId

class ConversationModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CONVERSATION_NAME.value]

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_CONVERSATION_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_CONVERSATION_NAME.value]
            indexes = Conversation.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )


    async def create_conversation(self, conversation: Conversation):
        now = datetime.datetime.utcnow()
        conversation.createdAt = now
        conversation.updatedAt = now

        result = await self.collection.insert_one(conversation.dict(by_alias=True, exclude_unset=True))
        conversation.id = result.inserted_id

        return conversation


    async def get_conversation_or_create_one(self, conversation_id: str, user_id: str):
        try:
            object_id = ObjectId(conversation_id)
        except InvalidId:
            object_id = None

        if object_id:
            record = await self.collection.find_one({
                "_id": object_id,
                "user_id": user_id,
            })
            if record:
                return Conversation(**record)

        # If not found or invalid id
        conversation = Conversation(title="", user_id=user_id)
        conversation = await self.create_conversation(conversation=conversation)
        return conversation


    # async def get_all_projects(self, page: int=1, page_size: int=10):

    #     # count total number of documents
    #     total_documents = await self.collection.count_documents({})

    #     # calculate total number of pages
    #     total_pages = total_documents // page_size
    #     if total_documents % page_size > 0:
    #         total_pages += 1

    #     cursor = self.collection.find().skip( (page-1) * page_size ).limit(page_size)
    #     projects = []
    #     async for document in cursor:
    #         projects.append(
    #             Conversation(**document)
    #         )

    #     return projects, total_pages
