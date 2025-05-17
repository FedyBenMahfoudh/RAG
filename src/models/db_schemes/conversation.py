from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId
import datetime

class Conversation(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    title: str
    user_id: str = Field(..., min_length=1)
    createdAt: Optional[datetime.datetime] = None
    updatedAt: Optional[datetime.datetime] = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [("user_id", 1)],
                "name": "user_id_index",
                "unique": False
            },
            {
                "key": [("user_id", 1), ("createdAt", -1)],
                "name": "user_id_createdAt_index",
                "unique": False
            }
        ]
