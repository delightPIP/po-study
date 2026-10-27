"""OpenAI 호출은 이 파일에서만. 키는 인자로만 받고 어디에도 남기지 않는다."""
import os

import openai

DEFAULT_MODEL = "gpt-6-luna"


def model_name():
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def stream_answer(api_key, prompt):
    """답을 조각조각 돌려준다. 실패하면 쉬운 말 한 줄만 담은 RuntimeError (원문 오류 · 키는 안 보여 줌)."""
    client = openai.OpenAI(api_key=api_key)
    try:
        events = client.responses.create(model=model_name(), input=prompt, stream=True)
        for event in events:
            if event.type == "response.output_text.delta":
                yield event.delta
    except openai.AuthenticationError:
        raise RuntimeError("키가 맞지 않아요. 키를 다시 확인해 주세요.") from None
    except openai.RateLimitError:
        raise RuntimeError("사용 한도를 넘었어요. 잠시 뒤에 다시 하거나 결제 한도를 확인해 주세요.") from None
    except openai.APIError:
        raise RuntimeError("AI 호출이 실패했어요. 잠시 뒤에 다시 해 주세요.") from None
