"""PO 프롬프트 스튜디오 — 화면만. 프롬프트 글은 tools.py, 예시는 examples.py, AI 호출은 llm.py."""
import os

import streamlit as st
from dotenv import load_dotenv

from examples import EXAMPLES, SERVICE_FIELDS
from llm import model_name, stream_answer
from tools import STAGES, TOOLS, ape_prompt, build_instructions, build_prompt, review_prompt, tools_in

st.set_page_config(page_title="PO 프롬프트 스튜디오", page_icon=":material/edit_note:", layout="wide",
                   initial_sidebar_state="expanded")
load_dotenv()  # 로컬에서만: .env 키를 키 칸 기본값으로 (배포 Secrets엔 키를 두지 않음)

DIRECT = "직접 입력"
WRITE_OWN = "직접 쓰기"
ACTIONS = {"run": "AI로 실행", "review": "⑫ 점검", "ape": "⑰ APE로 개선"}


def service_key(k):
    return f"svc_{k}"


def field_key(tool_id, k):
    return f"f_{tool_id}_{k}"


def default_value(src, service):
    """칸 기본값: '=글자'면 그 글자, 아니면 상황 블록의 그 칸, 없으면 빈칸."""
    if not src:
        return ""
    return src[1:] if src.startswith("=") else service.get(src, "")


def load_example():
    """예시를 고르면 상황 블록과, 상황 블록에서 기본값을 가져오는 칸을 채운다."""
    choice = st.session_state.example
    if choice == DIRECT:
        return
    data = EXAMPLES[choice]
    for k, _ in SERVICE_FIELDS:
        st.session_state[service_key(k)] = data.get(k, "")
    for tool in TOOLS:
        for k, _, _, src, _ in tool["fields"]:
            if src and not src.startswith("="):
                st.session_state[field_key(tool["id"], k)] = data.get(src, "")


def pass_answer(tool_id):
    """답을 고른 도구 칸으로 넘긴다 (콜백이라 그 칸이 이미 그려졌어도 안전)."""
    target = st.session_state[f"pass_{tool_id}"]
    st.session_state[target] = st.session_state.answers[tool_id]["text"]
    st.session_state.passed = target


# 다른 단계로 가면 안 보이는 칸의 값이 지워지므로, 매번 다시 담아 둔다
for k in list(st.session_state):
    if k.startswith(("f_", "svc_")):
        st.session_state[k] = st.session_state[k]
st.session_state.setdefault("answers", {})   # 도구별 마지막 답
st.session_state.setdefault("history", [])   # 내려받기용 기록 (키는 담지 않음)

# 넘길 수 있는 칸: 모든 도구의 긴 글 칸
PASS_TARGETS = {field_key(t["id"], k): f"{t['name']} · {label}"
                for t in TOOLS for k, label, kind, _, _ in t["fields"] if kind == "area"}

# ── 사이드바: 내 서비스 (⑭ 상황 블록) · 키 · 내려받기 ──
with st.sidebar:
    st.header("내 서비스")
    st.selectbox("예시 불러오기", [DIRECT, *EXAMPLES], key="example", on_change=load_example)
    for k, label in SERVICE_FIELDS:
        st.text_area(label, key=service_key(k), height=68, placeholder="비우면 '미정'")
    st.caption("여기 쓴 내용이 모든 프롬프트 맨 앞 [상황]에 들어가요.")

    st.header("AI 실행")
    api_key = st.text_input("OpenAI 키", type="password", value=os.getenv("OPENAI_API_KEY", ""),
                            placeholder="sk-로 시작하는 내 키",
                            help="이 화면에서만 쓰고 저장하지 않아요. 기록 · 내려받기에도 안 들어가요.")
    st.caption(f"모델: {model_name()} · 키가 없어도 프롬프트 조립 · 복사는 다 돼요.")

service = {k: st.session_state.get(service_key(k), "") for k, _ in SERVICE_FIELDS}

with st.sidebar:
    st.header("내려받기")
    history_md = "\n\n---\n\n".join(
        f"## {h['tool']} · {h['kind']}\n\n### 프롬프트\n\n```\n{h['prompt']}\n```\n\n### 답\n\n{h['answer']}"
        for h in st.session_state.history) or "아직 기록이 없어요."
    st.download_button("기록 (.md)", history_md, file_name="po-studio-기록.md",
                       icon=":material/download:", width="stretch")
    st.download_button("Claude 프로젝트 지침 (.md)", build_instructions(service),
                       file_name="PO도우미_지침.md", icon=":material/download:", width="stretch",
                       help="지금 서비스로 채운 #칸 형식 함수 상자 — Claude 프로젝트 지침에 붙여 넣기")

# ── 본문: 단계 → 도구 ──
st.title("PO 프롬프트 스튜디오")
st.caption("서비스 하나를 문제 발견부터 출시 후 회고까지. 단계 → 도구 → 칸 채우기 → 프롬프트 복사 · AI 실행")

if st.session_state.pop("passed", None):
    st.toast("답을 칸에 넣었어요. 그 단계로 가서 확인해 보세요.", icon=":material/check:")

stage = st.segmented_control(
    "단계", [s for s, _ in STAGES], format_func=dict(STAGES).get,
    default="s1", key="stage", label_visibility="collapsed",
) or "s1"

for tool in tools_in(stage):
    tid = tool["id"]
    with st.container(border=True):
        mark = "▶ " if tool["order"] == 1 else ""
        st.subheader(f"{mark}{tool['name']}")
        st.caption(f"{tool['tech']} · {tool['does']}")

        values = {}
        for k, label, kind, src, hint in tool["fields"]:
            key = field_key(tid, k)
            if kind == "choice":
                pick = st.selectbox(label, [*hint, WRITE_OWN], key=f"{key}_pick")
                values[k] = pick if pick != WRITE_OWN else st.text_input(
                    f"{label} — 직접 쓰기", key=key, placeholder="비우면 '미정'")
                continue
            if key not in st.session_state:
                st.session_state[key] = default_value(src, service)
            widget = st.text_input if kind == "text" else st.text_area
            values[k] = widget(label, key=key, placeholder=hint or "비우면 '미정'")

        prompt = build_prompt(tool, service, values)
        if prompt is None:
            st.info("이 도구의 프롬프트 문장은 아직 같이 다듬는 중이에요.", icon=":material/edit:")
            continue

        st.code(prompt, language=None, wrap_lines=True)
        st.caption(f"{len(prompt)}자 · 오른쪽 위 복사 버튼으로 복사")

        last = st.session_state.answers.get(tid)
        clicked = None
        with st.container(horizontal=True):
            for action, label in ACTIONS.items():
                needs_answer = action == "review" and not last
                if st.button(label, key=f"{tid}_{action}", disabled=not api_key or needs_answer,
                             help="키를 넣으면 열려요" if not api_key else
                             ("먼저 AI로 실행해 주세요" if needs_answer else None)):
                    clicked = action

        if clicked:
            sent = {"run": prompt, "review": review_prompt(prompt, last["text"] if last else ""),
                    "ape": ape_prompt(prompt)}[clicked]
            try:
                text = st.write_stream(stream_answer(api_key, sent))
            except RuntimeError as err:
                st.error(str(err), icon=":material/error:")
            else:
                text = text if isinstance(text, str) else "".join(text)
                st.session_state.answers[tid] = {"kind": ACTIONS[clicked], "text": text}
                st.session_state.history.append(
                    {"tool": tool["name"], "kind": ACTIONS[clicked], "prompt": sent, "answer": text})
                st.rerun()  # 저장된 답으로 다시 그려 [⑫ 점검] · 넘기기를 바로 열기
        elif last:
            st.markdown(f"**{last['kind']} 결과**")
            st.markdown(last["text"])

        if last:
            with st.container(horizontal=True, vertical_alignment="bottom"):
                targets = {k: v for k, v in PASS_TARGETS.items() if not k.startswith(f"f_{tid}_")}
                st.selectbox("이 답을 넘길 칸", list(targets), format_func=targets.get, key=f"pass_{tid}")
                st.button("칸에 넣기", key=f"{tid}_pass", on_click=pass_answer, args=(tid,),
                          icon=":material/arrow_forward:")
