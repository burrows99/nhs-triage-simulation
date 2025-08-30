import requests
import json
import time
from typing import Dict, Any, Optional
from .base import ModelProvider
import logging

logger = logging.getLogger(__name__)

class OllamaProvider(ModelProvider):
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.2:1b"):
        self.base_url = base_url
        self.model = model
        self.system_prompt = ""
        self.config = None
        
        # Default configuration
        self.timeout_sec = 45
        self.retries = 2
        self.options = {
            'temperature': 0.02,
            'top_p': 0.7,
            'num_predict': 75,
            'num_ctx': 1536,
            'num_gpu': -1,
            'num_thread': 4
        }
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the provider with Ollama settings"""
        self.config = config
        self.timeout_sec = config.get('timeout_sec', 45)
        self.retries = config.get('retries', 2)
        self.options.update(config.get('options', {}))
        
        logger.info(f"Ollama provider configured: timeout={self.timeout_sec}s, retries={self.retries}")
        logger.debug(f"Ollama options: {self.options}")
    
    def setup(self, system_prompt: str) -> None:
        """Initialize the model with system prompt"""
        self.system_prompt = system_prompt
        logger.debug(f"Ollama system prompt set: {system_prompt[:100]}...")
    
    def get_model_response(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Get raw model response with retry logic"""
        url = f"{self.base_url}/api/generate"
        
        # Merge options
        request_options = self.options.copy()
        if options:
            request_options.update(options)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": request_options
        }
        
        last_error = None
        
        for attempt in range(self.retries + 1):
            try:
                logger.debug(f"Ollama request attempt {attempt + 1}/{self.retries + 1}")
                
                response = requests.post(
                    url, 
                    json=payload, 
                    timeout=self.timeout_sec
                )
                response.raise_for_status()
                
                result = response.json()
                model_response = result.get('response', '')
                
                logger.debug(f"Ollama response received: {len(model_response)} characters")
                return model_response
                
            except requests.Timeout as e:
                last_error = f"Timeout after {self.timeout_sec}s: {str(e)}"
                logger.warning(f"Ollama timeout on attempt {attempt + 1}: {last_error}")
                
            except requests.RequestException as e:
                last_error = f"Request error: {str(e)}"
                logger.warning(f"Ollama request error on attempt {attempt + 1}: {last_error}")
                
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {str(e)}"
                logger.warning(f"Ollama JSON error on attempt {attempt + 1}: {last_error}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.retries:
                wait_time = 2 ** attempt
                logger.debug(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        logger.error(f"All Ollama attempts failed. Last error: {last_error}")
        return f"Error: {last_error}"
    
    def generate_triage_decision(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate triage decision for patient"""
        logger.debug(f"Generating triage decision with prompt length: {len(prompt)}")
        
        # Combine system prompt with user prompt if system prompt is set
        full_prompt = prompt
        if self.system_prompt:
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
        
        response = self.get_model_response(full_prompt, options)
        
        logger.debug(f"Triage decision response: {response[:200]}...")
        return response
    
    def validate_response(self, response: str) -> bool:
        """Validate if response is a valid JSON with required fields"""
        try:
            data = json.loads(response)
            required_fields = ['mts_priority', 'confidence', 'rationale']
            return all(field in data for field in required_fields)
        except (json.JSONDecodeError, TypeError):
            return False
    
    def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            # Check if our model is available
            models = response.json().get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            if self.model in model_names or any(self.model in name for name in model_names):
                logger.info(f"Ollama health check passed. Model '{self.model}' is available.")
                return True
            else:
                logger.warning(f"Model '{self.model}' not found. Available models: {model_names}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    def get_available_models(self) -> list:
        """Get list of available models"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            return [model.get('name', '') for model in models]
            
        except requests.RequestException as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return []