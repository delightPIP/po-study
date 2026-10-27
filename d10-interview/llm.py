"""OpenAI 호출은 이 파일에서만. 키는 인자로만 받고 어디에도 남기지 않는다."""
import json
import os

import openai

DEFAULT_MODEL = "gpt-6-luna"


def model_name():
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def ask_json(api_key, instructions, user_input, schema, name):
    """strict JSON 스키마로 답을 받아 dict로 돌려준다. 실패하면 쉬운 말 한 줄만 담은 RuntimeError (원문 오류 · 키는 안 보여 줌)."""
    client = openai.OpenAI(api_key=api_key)
    try:
        resp = client.responses.create(
            model=model_name(),
            instructions=instructions,
            input=user_input,
            text={"format": {"type": "json_schema", "name": name, "schema": schema, "strict": True}},
        )
        return json.loads(resp.output_text)
    except openai.AuthenticationError:
        raise RuntimeError("키가 맞지 않아요. 키를 다시 확인해 주세요.") from None
    except openai.RateLimitError:
        raise RuntimeError("사용 한도를 넘었어요. 잠시 뒤에 다시 하거나 결제 한도를 확인해 주세요.") from None
    except openai.APIError:
        raise RuntimeError("AI 호출이 실패했어요. 잠시 뒤에 다시 해 주세요.") from None
    except json.JSONDecodeError:
        raise RuntimeError("AI 답을 읽지 못했어요. 한 번 더 보내 주세요.") from None
