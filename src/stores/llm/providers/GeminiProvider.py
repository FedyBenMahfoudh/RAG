from ..LLMInterface import LLMInterface
from ..LLMEnums import GeminiEnums
import logging
from typing import Optional
from google import genai
from google.genai import types

class GeminiProvider(LLMInterface):
    def __init__(self, api_key: str, api_url: Optional[str] = None,
                 default_input_max_characters: int = 1000,
                 default_generation_max_output_tokens: int = 1000,
                 default_generation_temperature: float = 0.1):
        
        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        
        self.client = genai.Client(api_key=self.api_key)

        self.enums = GeminiEnums
        self.logger = logging.getLogger(__name__)
    
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list = [], max_output_tokens: int = None,
                      temperature: float = None):
        
        if not self.client:
            self.logger.error("Gemini client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model for Gemini was not set")
            return None
        
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        for content in chat_history:
            if content.get("role") == self.enums.SYSTEM.value:
                system_instruction = content.get("parts")[0].get("text")
                chat_history.remove(content)
                break

        chat_history.append(self.construct_prompt(prompt=prompt, role=self.enums.USER.value))

        response = self.client.models.generate_content(
            model=self.generation_model_id,
            contents=chat_history,
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                system_instruction=system_instruction,
            )
        )

        if not response or not response.text:
            self.logger.error("Error while generating text with Gemini")
            return None

        return response.text

    def embed_text(self, text: str, document_type: str = None):
        
        if not self.client:
            self.logger.error("Gemini client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for Gemini was not set")
            return None
        
        # Set task type (default to RETRIEVAL_DOCUMENT if not specified)
        task_type = "RETRIEVAL_DOCUMENT"
        if document_type == "QUERY":
            task_type = "RETRIEVAL_QUERY"
        if document_type == "DOCUMENT":
            task_type = "RETRIEVAL_DOCUMENT"

        try:
            # Generate embeddings
            response = self.client.models.embed_content(
                model=self.embedding_model_id,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                )
            )
            
            if hasattr(response, 'embedding') and response.embedding is not None:
                return response.embedding
            elif (hasattr(response, 'embeddings') and 
                isinstance(response.embeddings, list) and 
                len(response.embeddings) > 0 and 
                hasattr(response.embeddings[0], 'values')):
                return list(response.embeddings[0].values)
            else:
                self.logger.error("Unexpected embedding response format")
                return None
            
        except Exception as e:
            self.logger.error(f"Embedding failed: {str(e)}")
            return None

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "parts": [{"text": self.process_text(prompt)}]
        }
