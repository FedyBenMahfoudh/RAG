from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class Conversation(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    conversation_id: str = Field(..., min_length=1)
    user_id: str = Field(...,min_length=1)

    @validator('conversation_id')
    def validate_conversation_id(cls, value):
        if not value.isalnum():
            raise ValueError('conversation_id must be alphanumeric')
        
        return value

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def get_indexes(cls):

        return [
            {
                "key": [
                    ("conversation_id", 1)
                ],
                "name": "conversation_id_index_1",
                "unique": False
            },
            {
                "key": [
                    ("conversation_id", 1),
                    ("user_id",1)
                ],
                "name" : "conversation_id_user_id_index_1",
                "unique" :  True
            }
        ]