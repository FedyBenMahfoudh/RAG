import os

from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSignal

class ProjectController(BaseController):
    def __init__(self):
        super().__init__()

    def get_project_path(self, user_id: str):
        user_dir = os.path.join(self.file_dir, user_id)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        return user_dir