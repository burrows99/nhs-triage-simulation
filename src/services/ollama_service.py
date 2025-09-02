"""Ollama Service for LLM Integration

Provides integration with Ollama API for LLM-powered triage assessments.
"""

import json
import requests
from typing import Dict, Any, Optional
from src.logger import logger


class OllamaService:
    """Service for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 60):
        """Initialize Ollama service
        
        Args:
            base_url: Base URL for Ollama API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.api_url = f"{self.base_url}/api"
        
        logger.info(f"Initializing Ollama service at {self.base_url}")
        
    def check_health(self) -> bool:
        """Check if Ollama service is available
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            logger.debug("Checking Ollama service health")
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.debug("Ollama service is healthy")
            else:
                logger.warning(f"Ollama service health check failed: {response.status_code}")
                
            return is_healthy
            
        except Exception as e:
            logger.error(f"Ollama service health check failed: {e}")
            return False
    
    def list_models(self) -> Dict[str, Any]:
        """List available models
        
        Returns:
            Dictionary containing available models
        """
        try:
            logger.debug("Listing available Ollama models")
            response = requests.get(f"{self.api_url}/tags", timeout=self.timeout)
            response.raise_for_status()
            
            models = response.json()
            logger.debug(f"Available models: {[m.get('name', 'unknown') for m in models.get('models', [])]}")
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            raise RuntimeError(f"Cannot list Ollama models: {e}") from e
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None, 
                         model: str = "llama3.2:1b", temperature: float = 0.1, 
                         max_tokens: int = 500) -> str:
        """Generate response using Ollama API
        
        Args:
            prompt: User prompt for the model
            system_prompt: System prompt to set context
            model: Model name to use
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
            
        Raises:
            RuntimeError: If generation fails
        """
        logger.info(f"Generating response with model: {model}")
        logger.debug(f"Temperature: {temperature}, Max tokens: {max_tokens}")
        logger.debug(f"System prompt length: {len(system_prompt) if system_prompt else 0}")
        logger.debug(f"User prompt length: {len(prompt)}")
        
        # Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 4096,  # Context window
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
            logger.debug("System prompt included in request")
        
        try:
            logger.debug("Sending request to Ollama API")
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            logger.debug(f"Ollama API response status: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Ollama API response received: {len(str(result))} characters")
            
            # Extract generated text
            generated_text = result.get("response", "")
            
            if not generated_text:
                logger.error("Empty response from Ollama API")
                logger.error(f"Full response: {result}")
                raise RuntimeError("Ollama API returned empty response")
            
            logger.info(f"Response generated successfully: {len(generated_text)} characters")
            logger.debug(f"Generated text preview: {generated_text[:200]}..." if len(generated_text) > 200 else f"Generated text: {generated_text}")
            
            return generated_text
            
        except requests.exceptions.Timeout:
            logger.error(f"Ollama API request timed out after {self.timeout} seconds")
            raise RuntimeError(f"Ollama API timeout after {self.timeout} seconds")
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama API at {self.api_url}: {e}")
            raise RuntimeError(f"Ollama API connection failed: {e}") from e
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ollama API HTTP error: {e}")
            logger.error(f"Response content: {response.text if 'response' in locals() else 'No response'}")
            raise RuntimeError(f"Ollama API HTTP error: {e}") from e
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Ollama API: {e}")
            logger.error(f"Response text: {response.text if 'response' in locals() else 'No response'}")
            raise RuntimeError(f"Invalid JSON from Ollama API: {e}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error in Ollama API call: {type(e).__name__}: {e}")
            raise RuntimeError(f"Ollama API call failed: {e}") from e
    
    def pull_model(self, model_name: str) -> bool:
        """Pull/download a model
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            
            payload = {"name": model_name}
            response = requests.post(
                f"{self.api_url}/pull",
                json=payload,
                timeout=300,  # Longer timeout for model downloads
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            logger.info(f"Model {model_name} pulled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False