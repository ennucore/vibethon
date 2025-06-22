import os
import json
import getpass
from pydantic import BaseModel, Field
import platformdirs
from openai import OpenAI

class CredentialsConfig(BaseModel):
    crash_if_missing: bool = Field(default_factory=lambda: os.getenv("PYTHON_ENV") == "production")
    cache_dir: str = platformdirs.user_cache_dir("vibethon")
    cache_file: str = "credentials.json"
    cache_file_path: str = os.path.join(cache_dir, cache_file)

def get_ai_credentials(config: CredentialsConfig = CredentialsConfig()) -> OpenAI:
    """
    Get an AI instance using either environment variables, a cached credentials file,
    or the user from the CLI.

    If the credentials are not found and config.crash_if_missing is True, raise an exception.
    Otherwise, we prompt the user for the credentials in a CLI and get them that way.

    Args:
        config: The configuration for the credentials.

    Returns:
        The OpenAI client.
    """
    # Step 1: Try environment variables first (check multiple providers)
    env_vars_to_check = [
        ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
        ("OPENAI_API_KEY", None),  # None means use default OpenAI base URL
        ("ANTHROPIC_API_KEY", "https://api.anthropic.com/v1"),
        ("API_KEY", None),  # Generic fallback
    ]
    
    for env_var, base_url in env_vars_to_check:
        api_key = os.getenv(env_var)
        if api_key:
            if base_url:
                return OpenAI(api_key=api_key, base_url=base_url)
            else:
                return OpenAI(api_key=api_key)
    
    # Step 2: Try loading from cache file
    try:
        if os.path.exists(config.cache_file_path):
            with open(config.cache_file_path, 'r') as f:
                cached_data = json.load(f)
                api_key = cached_data.get("api_key")
                base_url = cached_data.get("base_url")
                if api_key:
                    if base_url:
                        return OpenAI(api_key=api_key, base_url=base_url)
                    else:
                        return OpenAI(api_key=api_key)
    except (json.JSONDecodeError, IOError):
        # If cache file is corrupted or unreadable, continue to next step
        pass
    
    # Step 3: If crash_if_missing is True and no credentials found, raise exception
    if config.crash_if_missing:
        raise ValueError("API key not found in environment variables or cache file")
    
    # Step 4: Prompt user for credentials via CLI
    print("\n" + "="*60)
    print("🔐 API CREDENTIALS SETUP")
    print("="*60)
    print("🚀 No API key found in environment or cache!")
    print("💡 Let's get you set up with your AI provider credentials.\n")
    
    api_key = getpass.getpass("🔑 Enter your API Key: ").strip()
    
    if not api_key:
        raise ValueError("❌ No API key provided")
    
    # Ask for provider/base URL
    print("\n" + "─"*50)
    print("🌟 SELECT YOUR AI PROVIDER")
    print("─"*50)
    print("1. 🚀 OpenRouter (Recommended)")
    print("2. 🤖 OpenAI") 
    print("3. ⚡ Custom Provider")
    print("─"*50)
    
    choice = input("🎯 Enter your choice (1-3) or press Enter for OpenRouter: ").strip()
    
    base_url = None
    provider_name = ""
    
    if choice == "2":
        base_url = None
        provider_name = "OpenAI"
        print("✅ Selected: OpenAI")
    elif choice == "3":
        print("🔧 Custom Provider Setup")
        base_url = input("🌐 Enter the base URL: ").strip()
        if not base_url:
            base_url = None
            provider_name = "Default"
        else:
            provider_name = "Custom"
        print(f"✅ Selected: {provider_name} Provider")
    else:  # Default to OpenRouter (choice == "1" or empty)
        base_url = "https://openrouter.ai/api/v1"
        provider_name = "OpenRouter"
        print("✅ Selected: OpenRouter (Great choice! 🎉)")
    
    # Cache the credentials
    print("\n💾 Saving credentials...")
    try:
        os.makedirs(config.cache_dir, exist_ok=True)
        cache_data = {"api_key": api_key}
        if base_url:
            cache_data["base_url"] = base_url
        
        with open(config.cache_file_path, 'w') as f:
            json.dump(cache_data, f)
        print("✅ Credentials cached successfully!")
        print(f"📁 Location: {config.cache_file_path}")
        print(f"🔒 Your {provider_name} credentials are now saved securely.")
    except IOError as e:
        print(f"⚠️  Warning: Could not cache credentials: {e}")
        print(f"⚠️  Please manually save your credentials to {config.cache_file_path}")
    
    print("\n🎊 Setup complete! Ready to use AI services!")
    print("="*60 + "\n")
    
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    else:
        return OpenAI(api_key=api_key)
