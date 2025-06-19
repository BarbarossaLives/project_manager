# AI Integration with Ollama for Project Planning
# This file serves as the main AI interface for the project manager

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

try:
    from config import config
    OLLAMA_BASE_URL = config.OLLAMA_BASE_URL
    OLLAMA_MODEL = config.OLLAMA_MODEL
except ImportError:
    # Fallback if config is not available
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.2"

logger = logging.getLogger(__name__)

class OllamaAI:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or OLLAMA_MODEL

    def is_available(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    def generate_response(self, prompt: str, system_prompt: str = None, timeout: int = 120) -> str:
        """Generate a response using Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            logger.info(f"Sending request to Ollama with model: {self.model}")

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                logger.info(f"Received response from Ollama: {len(ai_response)} characters")
                return ai_response
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "AI service temporarily unavailable"

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {timeout} seconds")
            return "AI request timed out - try a simpler request"
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama service")
            return "AI service not available - please ensure Ollama is running"
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return "AI service temporarily unavailable"

# Global AI instance
ollama_ai = OllamaAI()