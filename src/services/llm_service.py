"""
LLM Service Manager
Unified interface for OpenAI, Anthropic, and Kimi K2 (MoonShort AI)
"""

from typing import List, Dict, Any, Optional
import openai
from anthropic import Anthropic
import logging
from dataclasses import dataclass
import os
import requests

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM response wrapper"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    provider: str


class KimiK2Client:
    """Client for Kimi K2 LLM by MoonShot AI"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.ai/v1"):
        """
        Initialize Kimi K2 client (MoonShot AI)
        
        Args:
            api_key: Kimi K2 API key
            base_url: Base URL for MoonShot API (default: https://api.moonshot.ai/v1)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "kimi-k2-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Create chat completion using Kimi K2 API (MoonShot AI)
        
        Args:
            messages: List of message dicts
            model: Model identifier
            temperature: Response randomness
            max_tokens: Maximum response length
            
        Returns:
            Response dict compatible with OpenAI format
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kimi K2 API request failed: {e}")
            raise


class LLMService:
    """Unified LLM service supporting multiple providers"""
    
    # Supported providers
    PROVIDERS = {
        'openai': 'OpenAI GPT',
        'anthropic': 'Anthropic Claude',
        'kimi': 'Kimi K2 (MoonShot AI)'
    }
    
    def __init__(
        self,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        kimi_key: Optional[str] = None,
        kimi_base_url: Optional[str] = None,
        default_provider: str = "openai"
    ):
        """
        Initialize LLM service
        
        Args:
            openai_key: OpenAI API key
            anthropic_key: Anthropic API key
            kimi_key: Kimi K2 API key (MoonShort AI)
            kimi_base_url: Kimi K2 base URL (default: https://api.moonshot.cn/v1)
            default_provider: Default provider to use
        """
        self.default_provider = default_provider
        
        # Initialize OpenAI
        if openai_key:
            self.openai_client = openai.OpenAI(api_key=openai_key)
            logger.info("✅ OpenAI client initialized")
        else:
            self.openai_client = None
            logger.warning("⚠️  OpenAI client not initialized (no API key)")
        
        # Initialize Anthropic
        if anthropic_key:
            self.anthropic_client = Anthropic(api_key=anthropic_key)
            logger.info("✅ Anthropic client initialized")
        else:
            self.anthropic_client = None
            logger.warning("⚠️  Anthropic client not initialized (no API key)")
        
        # Initialize Kimi K2 (MoonShot AI)
        if kimi_key:
            self.kimi_client = KimiK2Client(
                api_key=kimi_key,
                base_url=kimi_base_url or "https://api.moonshot.ai/v1"
            )
            logger.info("✅ Kimi K2 (MoonShot AI) client initialized")
        else:
            self.kimi_client = None
            logger.warning("⚠️  Kimi K2 client not initialized (no API key)")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        provider: Optional[str] = None
    ) -> LLMResponse:
        """
        Send chat completion request
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (or None for default)
            temperature: Response randomness (0.0-2.0)
            max_tokens: Maximum response length
            provider: 'openai', 'anthropic', or 'kimi' (or None for default)
            
        Returns:
            LLMResponse object
            
        Raises:
            ValueError: If provider not available or unsupported
        """
        provider = provider or self.default_provider
        
        if provider not in self.PROVIDERS:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported: {list(self.PROVIDERS.keys())}"
            )
        
        # Route to appropriate provider
        if provider == "openai":
            return self._openai_chat(messages, model, temperature, max_tokens)
        elif provider == "anthropic":
            return self._anthropic_chat(messages, model, temperature, max_tokens)
        elif provider == "kimi":
            return self._kimi_chat(messages, model, temperature, max_tokens)
        else:
            raise ValueError(f"Provider {provider} not implemented")
    
    def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """OpenAI chat completion"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized (no API key)")
        
        # Default model from env or fallback
        model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens  # Updated parameter name
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                tokens_used=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason,
                provider='openai'
            )
            
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            raise
    
    def _anthropic_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Anthropic chat completion"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized (no API key)")
        
        # Default model from env or fallback
        model = model or os.getenv('ANTHROPIC_MODEL', 'claude-3-5-haiku-20241022')
        
        # Convert to Anthropic format (extract system message)
        system_msg = ""
        user_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_msg = msg['content']
            else:
                user_messages.append(msg)
        
        try:
            response = self.anthropic_client.messages.create(
                model=model,
                system=system_msg,
                messages=user_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return LLMResponse(
                content=response.content[0].text,
                model=model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason,
                provider='anthropic'
            )
            
        except Exception as e:
            logger.error(f"Anthropic request failed: {e}")
            raise
    
    def _kimi_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Kimi K2 chat completion (MoonShot AI)"""
        if not self.kimi_client:
            raise ValueError("Kimi K2 client not initialized (no API key)")
        
        # Default model from env or fallback
        model = model or os.getenv('KIMI_K2_MODEL', 'kimi-k2-turbo-preview')
        
        try:
            response = self.kimi_client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract from OpenAI-compatible format
            choice = response['choices'][0]
            usage = response.get('usage', {})
            
            return LLMResponse(
                content=choice['message']['content'],
                model=model,
                tokens_used=usage.get('total_tokens', 0),
                finish_reason=choice.get('finish_reason', 'stop'),
                provider='kimi'
            )
            
        except Exception as e:
            logger.error(f"Kimi K2 request failed: {e}")
            raise
    
    def get_available_providers(self) -> Dict[str, bool]:
        """
        Get list of available providers
        
        Returns:
            Dict mapping provider name to availability
        """
        return {
            'openai': self.openai_client is not None,
            'anthropic': self.anthropic_client is not None,
            'kimi': self.kimi_client is not None
        }
    
    def test_provider(self, provider: str) -> bool:
        """
        Test if a provider is working
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider works, False otherwise
        """
        try:
            test_messages = [
                {"role": "user", "content": "Say 'test successful' if you can read this."}
            ]
            
            response = self.chat(
                messages=test_messages,
                max_tokens=50,
                provider=provider
            )
            
            return "test successful" in response.content.lower()
            
        except Exception as e:
            logger.error(f"Provider {provider} test failed: {e}")
            return False


# Factory function
def get_llm_service() -> LLMService:
    """
    Get configured LLM service instance
    
    Returns:
        LLMService with providers from environment
    """
    return LLMService(
        openai_key=os.getenv('OPENAI_API_KEY'),
        anthropic_key=os.getenv('ANTHROPIC_API_KEY'),
        kimi_key=os.getenv('KIMI_K2_API_KEY'),
        kimi_base_url=os.getenv('KIMI_K2_BASE_URL'),
        default_provider=os.getenv('DEFAULT_LLM', 'openai')
    )


# Singleton instance
_llm_service = None

def get_global_llm_service() -> LLMService:
    """Get or create global LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = get_llm_service()
    return _llm_service
