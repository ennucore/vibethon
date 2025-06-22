"""
Elegant test suite for the auth module.
Tests cover all authentication scenarios with proper mocking and fixtures.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, mock_open, MagicMock
from openai import OpenAI

from auth import get_ai_credentials, CredentialsConfig


class TestCredentialsConfig:
    """Test the CredentialsConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CredentialsConfig()
        assert config.crash_if_missing == (os.getenv("PYTHON_ENV") == "production")
        assert "vibethon" in config.cache_dir
        assert config.cache_file == "credentials.json"
        assert config.cache_file_path.endswith("credentials.json")
    
    def test_production_config(self):
        """Test production environment configuration."""
        with patch.dict(os.environ, {"PYTHON_ENV": "production"}):
            config = CredentialsConfig()
            assert config.crash_if_missing is True
    
    def test_development_config(self):
        """Test development environment configuration."""
        with patch.dict(os.environ, {"PYTHON_ENV": "development"}):
            config = CredentialsConfig()
            assert config.crash_if_missing is False


class TestGetAICredentials:
    """Test the get_ai_credentials function with comprehensive scenarios."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CredentialsConfig()
            config.cache_dir = temp_dir
            config.cache_file_path = os.path.join(temp_dir, "test_credentials.json")
            config.crash_if_missing = False
            yield config
    
    @pytest.fixture
    def production_config(self):
        """Create a production configuration for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CredentialsConfig()
            config.cache_dir = temp_dir
            config.cache_file_path = os.path.join(temp_dir, "test_credentials.json")
            config.crash_if_missing = True
            yield config

    # Environment Variable Tests
    
    @pytest.mark.parametrize("env_var,expected_base_url", [
        ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
        ("OPENAI_API_KEY", None),
        ("ANTHROPIC_API_KEY", "https://api.anthropic.com/v1"),
        ("API_KEY", None),
    ])
    def test_env_var_success(self, mock_config, env_var, expected_base_url):
        """Test successful authentication using environment variables."""
        test_key = "test-api-key-123"
        
        with patch.dict(os.environ, {env_var: test_key}, clear=True):
            with patch('auth.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                result = get_ai_credentials(mock_config)
                
                if expected_base_url:
                    mock_openai.assert_called_once_with(api_key=test_key, base_url=expected_base_url)
                else:
                    mock_openai.assert_called_once_with(api_key=test_key)
                
                assert result == mock_client

    def test_env_var_priority(self, mock_config):
        """Test that environment variables are checked in correct priority order."""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "openrouter-key",
            "OPENAI_API_KEY": "openai-key",
            "API_KEY": "generic-key"
        }):
            with patch('auth.OpenAI') as mock_openai:
                get_ai_credentials(mock_config)
                # Should use OPENROUTER_API_KEY first
                mock_openai.assert_called_once_with(
                    api_key="openrouter-key", 
                    base_url="https://openrouter.ai/api/v1"
                )

    # Cache File Tests
    
    def test_cache_file_success(self, mock_config):
        """Test successful authentication from cache file."""
        cache_data = {
            "api_key": "cached-key-123",
            "base_url": "https://custom.api.com/v1"
        }
        
        with open(mock_config.cache_file_path, 'w') as f:
            json.dump(cache_data, f)
        
        with patch('auth.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            result = get_ai_credentials(mock_config)
            
            mock_openai.assert_called_once_with(
                api_key="cached-key-123",
                base_url="https://custom.api.com/v1"
            )
            assert result == mock_client

    def test_cache_file_no_base_url(self, mock_config):
        """Test cache file without base URL."""
        cache_data = {"api_key": "cached-key-123"}
        
        with open(mock_config.cache_file_path, 'w') as f:
            json.dump(cache_data, f)
        
        with patch('auth.OpenAI') as mock_openai:
            get_ai_credentials(mock_config)
            mock_openai.assert_called_once_with(api_key="cached-key-123")

    def test_cache_file_corrupted(self, mock_config):
        """Test handling of corrupted cache file."""
        # Create corrupted JSON file
        with open(mock_config.cache_file_path, 'w') as f:
            f.write("invalid json content")
        
        with patch('auth.OpenAI') as mock_openai:
            with patch('builtins.print') as mock_print:
                with patch('getpass.getpass', return_value="cli-key"):
                    with patch('builtins.input', return_value=""):  # Default to OpenRouter
                        get_ai_credentials(mock_config)
                        
                        # Should fall back to CLI prompt
                        mock_openai.assert_called_with(
                            api_key="cli-key",
                            base_url="https://openrouter.ai/api/v1"
                        )

    def test_cache_file_missing_key(self, mock_config):
        """Test cache file without API key."""
        cache_data = {"base_url": "https://some.api.com"}
        
        with open(mock_config.cache_file_path, 'w') as f:
            json.dump(cache_data, f)
        
        with patch('auth.OpenAI') as mock_openai:
            with patch('builtins.print') as mock_print:
                with patch('getpass.getpass', return_value="cli-key"):
                    with patch('builtins.input', return_value=""):
                        get_ai_credentials(mock_config)
                        
                        # Should fall back to CLI prompt
                        mock_openai.assert_called_with(
                            api_key="cli-key",
                            base_url="https://openrouter.ai/api/v1"
                        )

    # Production Mode Tests
    
    def test_production_mode_crash(self, production_config):
        """Test that production mode crashes when no credentials found."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key not found in environment variables or cache file"):
                get_ai_credentials(production_config)

    def test_production_mode_with_env_var(self, production_config):
        """Test that production mode works with environment variables."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "prod-key"}):
            with patch('auth.OpenAI') as mock_openai:
                get_ai_credentials(production_config)
                mock_openai.assert_called_once_with(
                    api_key="prod-key",
                    base_url="https://openrouter.ai/api/v1"
                )

    # CLI Interaction Tests
    
    def test_cli_openrouter_default(self, mock_config):
        """Test CLI with default OpenRouter selection."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('getpass.getpass', return_value="cli-key-123"):
                with patch('builtins.input', return_value=""):  # Default choice
                    with patch('builtins.print') as mock_print:
                        with patch('auth.OpenAI') as mock_openai:
                            get_ai_credentials(mock_config)
                            
                            mock_openai.assert_called_with(
                                api_key="cli-key-123",
                                base_url="https://openrouter.ai/api/v1"
                            )
                            
                            # Check that nice messages were printed
                            printed_messages = [call[0][0] for call in mock_print.call_args_list]
                            assert any("🔐 API CREDENTIALS SETUP" in msg for msg in printed_messages)
                            assert any("Great choice! 🎉" in msg for msg in printed_messages)

    def test_cli_openai_selection(self, mock_config):
        """Test CLI with OpenAI selection."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('getpass.getpass', return_value="openai-key"):
                with patch('builtins.input', return_value="2"):  # OpenAI choice
                    with patch('builtins.print'):
                        with patch('auth.OpenAI') as mock_openai:
                            get_ai_credentials(mock_config)
                            
                            mock_openai.assert_called_with(api_key="openai-key")

    def test_cli_custom_provider(self, mock_config):
        """Test CLI with custom provider selection."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('getpass.getpass', return_value="custom-key"):
                with patch('builtins.input', side_effect=["3", "https://custom.ai/v1"]):
                    with patch('builtins.print'):
                        with patch('auth.OpenAI') as mock_openai:
                            get_ai_credentials(mock_config)
                            
                            mock_openai.assert_called_with(
                                api_key="custom-key",
                                base_url="https://custom.ai/v1"
                            )

    def test_cli_empty_api_key(self, mock_config):
        """Test CLI with empty API key."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('getpass.getpass', return_value="   "):  # Empty/whitespace key
                with pytest.raises(ValueError, match="❌ No API key provided"):
                    get_ai_credentials(mock_config)

    # Caching Tests
    
    def test_cli_caching_success(self, mock_config):
        """Test that CLI input gets cached properly."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('getpass.getpass', return_value="cache-test-key"):
                with patch('builtins.input', return_value="2"):  # OpenAI
                    with patch('builtins.print'):
                        with patch('auth.OpenAI'):
                            get_ai_credentials(mock_config)
                            
                            # Check that cache file was created
                            assert os.path.exists(mock_config.cache_file_path)
                            
                            with open(mock_config.cache_file_path, 'r') as f:
                                cached_data = json.load(f)
                                assert cached_data["api_key"] == "cache-test-key"
                                assert "base_url" not in cached_data  # OpenAI has no base_url

    def test_cli_caching_with_base_url(self, mock_config):
        """Test caching with base URL."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('getpass.getpass', return_value="cache-key"):
                with patch('builtins.input', return_value=""):  # OpenRouter default
                    with patch('builtins.print'):
                        with patch('auth.OpenAI'):
                            get_ai_credentials(mock_config)
                            
                            with open(mock_config.cache_file_path, 'r') as f:
                                cached_data = json.load(f)
                                assert cached_data["api_key"] == "cache-key"
                                assert cached_data["base_url"] == "https://openrouter.ai/api/v1"

    def test_cli_caching_failure(self, mock_config):
        """Test handling of cache write failures."""
        # Make cache directory read-only to simulate write failure
        os.chmod(mock_config.cache_dir, 0o444)
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                with patch('getpass.getpass', return_value="key"):
                    with patch('builtins.input', return_value=""):
                        with patch('builtins.print') as mock_print:
                            with patch('auth.OpenAI'):
                                get_ai_credentials(mock_config)
                                
                                # Should print warning about cache failure
                                printed_messages = [call[0][0] for call in mock_print.call_args_list]
                                assert any("⚠️  Warning: Could not cache credentials" in msg for msg in printed_messages)
        finally:
            # Restore permissions for cleanup
            os.chmod(mock_config.cache_dir, 0o755)

    # Integration Tests
    
    def test_full_flow_env_to_cache(self, mock_config):
        """Test full flow: env var → cache → reuse cache."""
        # First call with env var
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}):
            with patch('auth.OpenAI') as mock_openai:
                result1 = get_ai_credentials(mock_config)
                mock_openai.assert_called_with(
                    api_key="env-key",
                    base_url="https://openrouter.ai/api/v1"
                )
        
        # Manually create cache (simulating CLI caching)
        cache_data = {
            "api_key": "cached-key",
            "base_url": "https://openrouter.ai/api/v1"
        }
        with open(mock_config.cache_file_path, 'w') as f:
            json.dump(cache_data, f)
        
        # Second call without env var should use cache
        with patch.dict(os.environ, {}, clear=True):
            with patch('auth.OpenAI') as mock_openai:
                result2 = get_ai_credentials(mock_config)
                mock_openai.assert_called_with(
                    api_key="cached-key",
                    base_url="https://openrouter.ai/api/v1"
                )


# Test Fixtures and Utilities

@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    env_vars_to_clean = [
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY", 
        "ANTHROPIC_API_KEY",
        "API_KEY",
        "PYTHON_ENV"
    ]
    
    original_values = {}
    for var in env_vars_to_clean:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 