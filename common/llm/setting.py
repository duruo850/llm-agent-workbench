from common.env import (
    get_ollama_base_url,
    get_ollama_text_model,
    get_ollama_vision_model,
    is_deepseek_use_system_proxy,
)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

OLLAMA_BASE_URL = get_ollama_base_url()
OLLAMA_VISION_MODEL = get_ollama_vision_model()
OLLAMA_TEXT_MODEL = get_ollama_text_model()


def use_system_proxy() -> bool:
    return is_deepseek_use_system_proxy()
