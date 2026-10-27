"""질문 고르기 · 진행 규칙 · 숫자 계산 (AI 없음)."""
import random

import pandas as pd

TOTAL_QUESTIONS = 5
MAX_FOLLOW_UPS = 1
MAX_UNDERSTANDING_STEP = 25
INTRO = "1분 동안 자기소개를 해 주세요."


def load_questions(path):
    return pd.read_csv(path, encoding="utf-8-sig")


def _one(rows, rng):
    row = rows.iloc[rng.randrange(len(rows))]
    return {"question": row["질문"], "type": row["유형"], "point": row["보는 점"]}


def pick_questions(df, job, seed=None):
    """자기소개 1 + 공통 1(자기소개 제외) + 직무 1 + 경험 1 + 상황 1 = 5개, 이 순서로."""
    rng = random.Random(seed)
    common = df[df["직군"] == "공통"]
    mine = df[df["직군"] == job]
    picked = [
        _one(common[common["질문"] == INTRO], rng),
        _one(common[common["질문"] != INTRO], rng),
        _one(mine[mine["유형"] == "직무"], rng),
        _one(mine[mine["유형"] == "경험"], rng),
        _one(mine[mine["유형"] == "상황"], rng),
    ]
    assert len(picked) == TOTAL_QUESTIONS
    return picked


def next_step(follow_up, clarify, used):
    """clarify → 같은 질문 유지(횟수 안 셈) / follow_up 이고 한도 안 → 꼬리 질문 / 그 외 → 다음 질문."""
    if clarify:
        return "clarify"
    if follow_up and used < MAX_FOLLOW_UPS:
        return "follow_up"
    return "next"


def clamp(x, lo, hi):
    try:
        x = int(x)
    except (TypeError, ValueError):
        x = lo
    return max(lo, min(hi, x))


def smooth(prev, new):
    """이해도가 한 번에 25 넘게 바뀌면 25까지만 반영."""
    new = clamp(new, 0, 100)
    step = max(-MAX_UNDERSTANDING_STEP, min(MAX_UNDERSTANDING_STEP, new - prev))
    return prev + step


def dialogue_text(turns):
    """이번 질문에서 오간 대화를 순서대로 (INTERVIEWER 의 [입력])."""
    names = {"question": "질문", "follow_up": "꼬리 질문", "clarify": "다시 묻기", "answer": "지원자 답"}
    return "\n".join(f"{names[t['kind']]}: {t['text']}" for t in turns)
