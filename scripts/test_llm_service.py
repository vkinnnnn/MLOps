"""
Test script for LLM Service with Kimi K2 (MoonShort AI)
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


def test_provider_availability():
    """Test which providers are available"""
    print("\n" + "="*60)
    print("Test 1: Provider Availability")
    print("="*60)
    
    try:
        llm_service = LLMService(
            openai_key=os.getenv('OPENAI_API_KEY'),
            anthropic_key=os.getenv('ANTHROPIC_API_KEY'),
            kimi_key=os.getenv('KIMI_K2_API_KEY'),
            kimi_base_url=os.getenv('KIMI_K2_BASE_URL'),
            default_provider=os.getenv('DEFAULT_LLM', 'openai')
        )
        
        available = llm_service.get_available_providers()
        
        print("\nProvider Status:")
        for provider, is_available in available.items():
            status = "Available" if is_available else "Not configured"
            icon = "✓" if is_available else "✗"
            print(f"  {icon} {provider.capitalize()}: {status}")
        
        return llm_service, any(available.values())
        
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        return None, False


def test_simple_completion(llm_service, provider):
    """Test simple completion with a provider"""
    print(f"\n" + "="*60)
    print(f"Test 2: {provider.capitalize()} Simple Completion")
    print("="*60)
    
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from integration test!' and nothing else."}
        ]
        
        print(f"\nSending request to {provider}...")
        response = llm_service.chat(
            messages=messages,
            max_tokens=50,
            temperature=0.3,
            provider=provider
        )
        
        print(f"  ✓ Response received!")
        print(f"  Model: {response.model}")
        print(f"  Provider: {response.provider}")
        print(f"  Tokens: {response.tokens_used}")
        print(f"  Content: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_financial_query(llm_service, provider):
    """Test financial domain query"""
    print(f"\n" + "="*60)
    print(f"Test 3: {provider.capitalize()} Financial Query")
    print("="*60)
    
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a financial advisor helping students understand loan terms."
            },
            {
                "role": "user",
                "content": "In one sentence, what is a prepayment penalty?"
            }
        ]
        
        print(f"\nQuerying {provider} about prepayment penalties...")
        response = llm_service.chat(
            messages=messages,
            max_tokens=100,
            temperature=0.5,
            provider=provider
        )
        
        print(f"  ✓ Response received!")
        print(f"  Tokens used: {response.tokens_used}")
        print(f"  Answer: {response.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_kimi_k2_specifically():
    """Test Kimi K2 (MoonShort AI) specifically"""
    print("\n" + "="*60)
    print("Test 4: Kimi K2 (MoonShort AI) Specific Test")
    print("="*60)
    
    kimi_key = os.getenv('KIMI_K2_API_KEY')
    
    if not kimi_key or kimi_key == 'your-kimi-k2-key-here':
        print("  ⏭️  Skipping (Kimi K2 not configured)")
        return False
    
    try:
        llm_service = LLMService(
            kimi_key=kimi_key,
            kimi_base_url=os.getenv('KIMI_K2_BASE_URL', 'https://api.moonshot.cn/v1'),
            default_provider='kimi'
        )
        
        messages = [
            {"role": "user", "content": "Respond with 'Kimi K2 is working!' if you receive this."}
        ]
        
        print("\nSending test request to Kimi K2 (MoonShort AI)...")
        response = llm_service.chat(
            messages=messages,
            max_tokens=50,
            provider='kimi'
        )
        
        print(f"  ✓ Kimi K2 responded!")
        print(f"  Model: {response.model}")
        print(f"  Content: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Kimi K2 test failed: {e}")
        print(f"\nNote: If MoonShort API endpoint is different, update KIMI_K2_BASE_URL in .env")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("LLM Service Test Suite")
    print("Testing OpenAI, Anthropic, and Kimi K2 (MoonShort AI)")
    print("="*60)
    
    # Test 1: Provider availability
    llm_service, has_providers = test_provider_availability()
    
    if not has_providers:
        print("\n" + "="*60)
        print("❌ No LLM providers configured!")
        print("="*60)
        print("\nPlease add API keys to .env file:")
        print("  OPENAI_API_KEY=sk-...")
        print("  ANTHROPIC_API_KEY=sk-ant-...")
        print("  KIMI_K2_API_KEY=sk-...")
        return
    
    # Test available providers
    available = llm_service.get_available_providers()
    
    # Test 2 & 3: Run tests for each available provider
    results = {}
    for provider, is_available in available.items():
        if is_available:
            simple_ok = test_simple_completion(llm_service, provider)
            financial_ok = test_financial_query(llm_service, provider)
            results[provider] = simple_ok and financial_ok
        else:
            results[provider] = None
    
    # Test 4: Kimi K2 specific test
    if available.get('kimi'):
        kimi_ok = test_kimi_k2_specifically()
        if kimi_ok:
            results['kimi_specific'] = True
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for provider, result in results.items():
        if result is True:
            print(f"  ✓ {provider.capitalize()}: All tests passed")
        elif result is False:
            print(f"  ✗ {provider.capitalize()}: Tests failed")
        else:
            print(f"  ⏭️  {provider.capitalize()}: Not configured")
    
    # Overall status
    passed = sum(1 for r in results.values() if r is True)
    tested = sum(1 for r in results.values() if r is not None)
    
    print()
    if passed == tested and tested > 0:
        print("🎉 All available providers working correctly!")
        print("\nYou can now:")
        print("  1. Use LLM service in your application")
        print("  2. Build the RAG chatbot")
        print("  3. Create hybrid queries")
    elif passed > 0:
        print(f"⚠️  {passed}/{tested} providers working")
        print("\nWorking providers can be used for development.")
    else:
        print("❌ No providers working correctly")
        print("\nPlease check:")
        print("  - API keys are valid")
        print("  - Network connection is active")
        print("  - Provider endpoints are accessible")
    
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
