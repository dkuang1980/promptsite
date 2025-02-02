import pytest
from unittest.mock import Mock, patch

from promptsite.llm import OpenAiLLM, OllamaLLM, AnthropicLLM
from promptsite.exceptions import ConfigError

@pytest.fixture
def mock_openai_response():
    return Mock(choices=[Mock(message=Mock(content="OpenAI response"))])

@pytest.fixture
def mock_ollama_response():
    return Mock(message=Mock(content="Ollama response"))

@pytest.fixture
def mock_anthropic_response():
    return Mock(content="Anthropic response")

def test_openai_initialization():
    """Test OpenAI LLM initialization."""
    config = {"model": "gpt-4"}
    with patch('openai.OpenAI'):
        llm = OpenAiLLM(config)
        assert llm.config == config

def test_openai_initialization_no_model():   
    """Test OpenAI LLM initialization without model."""
    with patch('openai.OpenAI'):
        with pytest.raises(ConfigError) as exc_info:
            OpenAiLLM({})
    assert str(exc_info.value) == "LLM model is not set in config"

@patch('openai.OpenAI')
def test_openai_run(mock_openai_class, mock_openai_response):
    """Test OpenAI LLM run method."""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai_class.return_value = mock_client

    config = {"model": "gpt-4", "temperature": 0.7}
    llm = OpenAiLLM(config)
    
    response = llm.run("Test prompt")
    assert response == "OpenAI response"
        
    response = llm.run("Test prompt", temperature=0.1)
    
    # Verify the call
    assert mock_client.chat.completions.create.call_count == 2
    mock_client.chat.completions.create.assert_any_call(
        messages=[{"role": "user", "content": "Test prompt"}],
        model="gpt-4",
        temperature=0.7
    )
    mock_client.chat.completions.create.assert_any_call(
        messages=[{"role": "user", "content": "Test prompt"}],
        model="gpt-4",
        temperature=0.1
    )

@patch('openai.OpenAI')
def test_openai_run_with_system_prompt(mock_openai_class, mock_openai_response):
    """Test OpenAI LLM run method with system prompt."""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    mock_openai_class.return_value = mock_client

    config = {"model": "gpt-4"}
    llm = OpenAiLLM(config)
    
    response = llm.run("Test prompt", system_prompt="System instruction")
    assert response == "OpenAI response"
    
    # Verify the call includes system message
    mock_client.chat.completions.create.assert_called_once_with(
        messages=[
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "Test prompt"}
        ],
        model="gpt-4"
    )

def test_ollama_initialization():
    """Test Ollama LLM initialization."""
    config = {"model": "llama2"}
    llm = OllamaLLM(config)
    assert llm.config == config

@patch('ollama.chat')
def test_ollama_run(mock_chat, mock_ollama_response):
    """Test Ollama LLM run method."""
    mock_chat.return_value = mock_ollama_response
    
    config = {"model": "llama2"}
    llm = OllamaLLM(config)
    
    response = llm.run("Test prompt")
    assert response == "Ollama response"
    
    response = llm.run("Test prompt", model="llama3.1")

    # Verify the call
    assert mock_chat.call_count == 2
    mock_chat.assert_any_call(
        messages=[{"role": "user", "content": "Test prompt"}],
        model="llama2"
    )
    mock_chat.assert_any_call(
        messages=[{"role": "user", "content": "Test prompt"}],
        model="llama3.1"
    )

@patch('ollama.chat')
def test_ollama_run_with_system_prompt(mock_chat, mock_ollama_response):
    """Test Ollama LLM run method with system prompt."""
    mock_chat.return_value = mock_ollama_response
    
    config = {"model": "llama2"}
    llm = OllamaLLM(config)
    
    response = llm.run("Test prompt", system_prompt="System instruction")
    assert response == "Ollama response"
    
    # Verify the call includes system message
    mock_chat.assert_called_once_with(
        messages=[
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "Test prompt"}
        ],
        model="llama2"
    )

def test_anthropic_initialization():
    """Test Anthropic LLM initialization."""
    config = {"model": "claude-3-opus-20240229"}
    with patch('anthropic.Anthropic'):
        llm = AnthropicLLM(config)
        assert llm.config == config

@patch('anthropic.Anthropic')
def test_anthropic_run(mock_anthropic_class, mock_anthropic_response):
    """Test Anthropic LLM run method."""
    mock_client = Mock()
    mock_client.messages.create.return_value = mock_anthropic_response
    mock_anthropic_class.return_value = mock_client

    config = {"model": "claude-3-opus-20240229"}
    llm = AnthropicLLM(config)
    
    response = llm.run("Test prompt")
    assert response == "Anthropic response"
    
    response = llm.run("Test prompt", model="claude-3-5-sonnet-20240620")
    
    # Verify the call
    assert mock_client.messages.create.call_count == 2
    mock_client.messages.create.assert_any_call(
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": "Test prompt"}]
        }],
        model="claude-3-opus-20240229"
    )
    mock_client.messages.create.assert_any_call(
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": "Test prompt"}]
        }],
        model="claude-3-5-sonnet-20240620"
    )

@patch('anthropic.Anthropic')
def test_anthropic_run_with_system_prompt(mock_anthropic_class, mock_anthropic_response):
    """Test Anthropic LLM run method with system prompt."""
    mock_client = Mock()
    mock_client.messages.create.return_value = mock_anthropic_response
    mock_anthropic_class.return_value = mock_client

    config = {"model": "claude-3-opus-20240229"}
    llm = AnthropicLLM(config)
    
    response = llm.run("Test prompt", system_prompt="System instruction")
    assert response == "Anthropic response"
    
    # Verify the call includes system instruction
    mock_client.messages.create.assert_called_once_with(
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": "Test prompt"}]
        }],
        model="claude-3-opus-20240229",
        system="System instruction"
    )
