from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSignal
import os

class ConversationController(BaseController):
    
    def __init__(self):
        super().__init__()

    def get_conversation_path(self, conversation_id: str,user_id:str):
        conversation_dir = os.path.join(
            self.files_dir,
            user_id,
            conversation_id
        )

        if not os.path.exists(conversation_dir):
            os.makedirs(conversation_dir)

        return conversation_dir

    
