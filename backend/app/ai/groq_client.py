import os
from typing import Tuple
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Ensure environment variables are loaded
load_dotenv()


class GroqConfigurationError(Exception):
    """Raised when Groq API key or model configuration is missing or invalid."""
    pass


def get_groq_config() -> Tuple[str, str]:
    """
    Retrieves and validates Groq configuration from server-side environment.
    
    Security & Architecture Rules:
    - Never hard-codes API keys or model names.
    - Strictly server-side: GROQ_API_KEY is never sent to clients or browser.
    - Fails gracefully with a clear exception if configuration is missing.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model_name = os.getenv("GROQ_MODEL", "").strip()

    if not api_key or api_key == "your_groq_api_key_here":
        raise GroqConfigurationError(
            "GROQ_API_KEY is not configured. "
            "Please add your Groq API key to backend/.env (e.g., GROQ_API_KEY=gsk_...)."
        )

    if not model_name or model_name in ("your_supported_model_here", "your_groq_model_here"):
        raise GroqConfigurationError(
            "GROQ_MODEL is not configured. "
            "Please set a valid, currently supported Groq model name in backend/.env (e.g., GROQ_MODEL=llama-3.3-70b-versatile)."
        )

    return api_key, model_name


def is_groq_configured() -> bool:
    """Checks whether valid Groq credentials and model name are present."""
    try:
        get_groq_config()
        return True
    except GroqConfigurationError:
        return False


def get_chat_groq(temperature: float = 0.0) -> ChatGroq:
    """
    Initializes and returns a ChatGroq client configured from environment variables.
    Default temperature is 0.0 for deterministic factual extraction.
    """
    api_key, model_name = get_groq_config()
    return ChatGroq(
        api_key=api_key,
        model=model_name,
        temperature=temperature,
    )
