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


# ───────── 평가 (STEP 3) ─────────
CRITERIA = [("specific", "구체성"), ("relevance", "직무 연관"), ("structure", "구조"), ("evidence", "근거 · 검증")]
REWRITE_UNDER = 14  # 답 합계(0~20)가 이 점수 미만이면 고친 답을 보여 줌


def transcript_text(transcript):
    """평가 위원회에 넘길 면접 기록 전체."""
    blocks = []
    for i, item in enumerate(transcript, 1):
        blocks.append(f"[답변 {i}] ({item['type']}) {item['question']}\n보는 점: {item['point']}\n{dialogue_text(item['turns'])}")
    return "\n\n".join(blocks)


def panel_average(panel):
    """위원 점수(0~10) 평균, 소수 1자리."""
    if not panel:
        return 0.0
    return round(sum(clamp(m["score"], 0, 10) for m in panel) / len(panel), 1)


def answer_total(a):
    """기준 4개(각 0~5) 합 0~20."""
    return sum(clamp(a[k], 0, 5) for k, _ in CRITERIA)


def needs_rewrite(total):
    return total < REWRITE_UNDER


def normalize_eval(raw, count):
    """AI가 준 평가를 코드 기준으로 정리: 점수 자르기 · 합계 다시 계산 · 답변 번호 맞추기."""
    panel = [{**m, "score": clamp(m["score"], 0, 10)} for m in raw["panel"]]
    by_no = {}
    for a in raw["answers"]:
        no = clamp(a["no"], 1, count)
        if no not in by_no:
            fixed = {**a, "no": no, **{k: clamp(a[k], 0, 5) for k, _ in CRITERIA}}
            fixed["total"] = answer_total(fixed)
            fixed["show_rewrite"] = needs_rewrite(fixed["total"])
            by_no[no] = fixed
    answers = [by_no.get(n) for n in range(1, count + 1)]  # 빠진 답은 None
    totals = [a["total"] for a in answers if a]
    return {
        "panel": panel,
        "panel_average": panel_average(panel),
        "conflict": raw["conflict"],
        "agree": raw["agree"],
        "answers": answers,
        "answer_average": round(sum(totals) / len(totals), 1) if totals else 0.0,
        "next": raw["next"][:3],
    }


# ───────── 재도전 (STEP 4) ─────────
def my_answers(item):
    """그 질문에서 내가 한 답(꼬리 질문 답 포함)을 이어서."""
    return " / ".join(t["text"] for t in item["turns"] if t["kind"] == "answer")


def retry_input(item, answer):
    return f"[질문] {item['question']}\n[보는 점] {item['point']}\n[지원자 답] {answer}"


def normalize_scores(raw):
    """재채점 결과: 점수 자르기 + 합계 다시 계산."""
    fixed = {k: clamp(raw[k], 0, 5) for k, _ in CRITERIA}
    return {**fixed, "total": answer_total(fixed), "weak": raw["weak"]}


def lowest_first(answers):
    """평가받은 답 번호(1부터)를 합계 낮은 순으로."""
    rated = [(a["total"], a["no"]) for a in answers if a]
    return [no for _, no in sorted(rated)]


def compare(before, after):
    """전 · 후 합계와 차이, 기준별 전/후."""
    rows = [{"기준": name, "전": before[k], "후": after[k], "차이": after[k] - before[k]} for k, name in CRITERIA]
    return {"before": before["total"], "after": after["total"], "diff": after["total"] - before["total"], "rows": rows}


# ───────── PO 케이스 면접 (STEP 5) ─────────
CASE_JOB = "PO"
CASE_STEPS = 6
CASE_CRITERIA = [("problem", "문제 정의"), ("priority", "우선순위 근거"), ("metric", "지표 · 검증"), ("scope", "범위 · 소통")]


def load_voc(path):
    return pd.read_csv(path, encoding="utf-8-sig")


def voc_text(voc):
    return "\n".join(f"{r['번호']}. {r['VOC']} (지난주 {r['지난주 건수']}건)" for _, r in voc.iterrows())


def normalize_case(raw):
    """케이스 평가 정리: 점수 자르기 · 합계 다시 계산 · 빠진 단계 찾기."""
    scores = {k: clamp(raw[k], 0, 5) for k, _ in CASE_CRITERIA}
    steps = {}
    for s in raw["steps"]:
        n = clamp(s["step"], 1, CASE_STEPS)
        steps.setdefault(n, s["conclusion"])
    total = sum(scores.values())
    return {
        **scores,
        "total": total,
        "show_better": needs_rewrite(total),
        "steps": [(n, steps[n]) for n in sorted(steps)],
        "missing_steps": [n for n in range(1, CASE_STEPS + 1) if n not in steps],
        "weak": raw["weak"],
        "better": raw["better"],
    }
