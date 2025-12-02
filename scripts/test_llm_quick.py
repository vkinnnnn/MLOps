"""
Quick LLM Service Test (No Unicode)
Tests all three providers: OpenAI, Anthropic, and Kimi K2
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.services.llm_service import LLMService

# Load environment
load_dotenv(project_root / '.env')


def main():
    print("="*60)
    print("LLM Service Quick Test")
    print("="*60)
    
    # Initialize service
    print("\nInitializing LLM service...")
    try:
        llm_service = LLMService(
            openai_key=os.getenv('OPENAI_API_KEY'),
            anthropic_key=os.getenv('ANTHROPIC_API_KEY'),
            kimi_key=os.getenv('KIMI_K2_API_KEY'),
            kimi_base_url=os.getenv('KIMI_K2_BASE_URL'),
            default_provider=os.getenv('DEFAULT_LLM', 'openai')
        )
        print("SUCCESS: LLM service initialized")
    except Exception as e:
        print(f"FAILED: {e}")
        return
    
    # Check available providers
    print("\nChecking available providers...")
    available = llm_service.get_available_providers()
    
    for provider, is_available in available.items():
        status = "Available" if is_available else "Not configured"
        print(f"  {provider}: {status}")
    
    # Test each available provider
    print("\n" + "="*60)
    print("Testing Available Providers")
    print("="*60)
    
    for provider, is_available in available.items():
        if not is_available:
            continue
        
        print(f"\nTesting {provider.upper()}...")
        
        try:
            response = llm_service.chat(
                messages=[
                    {"role": "user", "content": "Say 'Hello from integration test!' and nothing else."}
                ],
                max_tokens=50,
                temperature=0.3,
                provider=provider
            )
            
            print(f"  SUCCESS!")
            print(f"  Model: {response.model}")
            print(f"  Tokens: {response.tokens_used}")
            print(f"  Response: {response.content[:100]}")
            
        except Exception as e:
            print(f"  FAILED: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    working = sum(1 for available in llm_service.get_available_providers().values() if available)
    print(f"Available providers: {working}/3")
    
    if working == 3:
        print("\nSUCCESS: All 3 LLM providers are working!")
        print("  - OpenAI GPT-4")
        print("  - Anthropic Claude")
        print("  - Kimi K2 (MoonShort AI)")
    elif working > 0:
        print(f"\nPARTIAL: {working} provider(s) working")
    else:
        print("\nFAILED: No providers available")
    
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
