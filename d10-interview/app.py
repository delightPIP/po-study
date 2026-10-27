"""AI 면접 코치 — Streamlit 화면만. 프롬프트는 prompts.py, AI 호출은 llm.py, 계산은 coach.py."""
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

import coach
import prompts
from llm import ask_json, model_name

load_dotenv()  # 로컬에서만: .env 키를 키 칸 기본값으로 (배포에는 키를 두지 않음)

HERE = Path(__file__).parent
# 배포판은 PO만. 로컬에서 다른 직군도 보려면 .env 에 INTERVIEW_JOBS=PO,개발,디자인,마케팅
ENABLED_JOBS = [j.strip() for j in os.getenv("INTERVIEW_JOBS", "PO").split(",") if j.strip() in prompts.PERSONAS]
EXAMPLE = {  # data/PO_예시답변.md 의 가상 지원자 (공개용)
    "f_name": "윤하늘",
    "f_company": "클래스로",
    "f_experience": "온라인 교육 회사(가상)에서 웹 개발을 3년 했음. 요청받은 대로 만든 수강 후기 기능이 출시 후 거의 쓰이지 않는 것을 보고, "
                    "무엇을 왜 만들지 정하는 일의 중요성을 알게 되어 PO로 전환하려 함.",
}
STATE_KEYS = ["profile", "questions", "q_index", "follow_ups_used", "messages", "transcript", "understanding", "finished"]

st.set_page_config(page_title="AI 면접 코치", page_icon="🎤")
ss = st.session_state


def reset():
    for k in STATE_KEYS:
        ss.pop(k, None)


def fill_example():
    ss.update(EXAMPLE)


def say(text):
    ss.messages.append({"role": "assistant", "content": text})


def start(profile):
    df = coach.load_questions(HERE / "data" / "questions.csv")
    ss.profile = profile
    ss.questions = coach.pick_questions(df, profile["job"])
    ss.q_index, ss.follow_ups_used, ss.understanding, ss.finished = 0, 0, 0, False
    ss.messages = []
    q = ss.questions[0]
    ss.transcript = [{**q, "turns": [{"kind": "question", "text": q["question"]}], "blocked_follow_up": False}]
    say(f"안녕하세요, {profile['name']}님. {profile['company']} {profile['job']} 신입 모의면접을 시작할게요. "
        f"질문은 {coach.TOTAL_QUESTIONS}개예요.\n\n**질문 1/{coach.TOTAL_QUESTIONS}** {q['question']}")


def handle_answer(api_key, answer):
    item = ss.transcript[ss.q_index]
    item["turns"].append({"kind": "answer", "text": answer})
    p = ss.profile
    context = prompts.CONTEXT.format(company=p["company"], job=p["job"], experience=p["experience"])
    instructions = prompts.INTERVIEWER.format(persona=prompts.PERSONAS[p["job"]], context=context,
                                              question=item["question"], point=item["point"])
    try:
        r = ask_json(api_key, instructions, coach.dialogue_text(item["turns"]), prompts.INTERVIEWER_SCHEMA, "interviewer")
    except RuntimeError:
        item["turns"].pop()  # 실패한 답은 기록에서 빼고 다시 보낼 수 있게
        raise

    ss.messages.append({"role": "user", "content": answer})
    ss.understanding = coach.smooth(ss.understanding, r["understanding"])
    reaction, asked = r["reaction"].strip(), r["question"].strip()
    step = coach.next_step(r["follow_up"], r["clarify"], ss.follow_ups_used)

    if step == "clarify":
        asked = asked or item["question"]
        item["turns"].append({"kind": "clarify", "text": asked})
        say("\n\n".join(x for x in [reaction, asked] if x))
    elif step == "follow_up" and asked:
        ss.follow_ups_used += 1
        item["turns"].append({"kind": "follow_up", "text": asked})
        say("\n\n".join(x for x in [reaction, "↪ " + asked] if x))
    else:
        if r["follow_up"]:
            item["blocked_follow_up"] = True  # AI는 더 묻자고 했지만 코드가 막음
        ss.q_index += 1
        ss.follow_ups_used = 0
        if ss.q_index < coach.TOTAL_QUESTIONS:
            q = ss.questions[ss.q_index]
            ss.transcript.append({**q, "turns": [{"kind": "question", "text": q["question"]}], "blocked_follow_up": False})
            say("\n\n".join(x for x in [reaction, f"**질문 {ss.q_index + 1}/{coach.TOTAL_QUESTIONS}** {q['question']}"] if x))
        else:
            ss.finished = True
            say("\n\n".join(x for x in [reaction, "면접은 여기까지예요. 수고하셨어요."] if x))


# ───────── 사이드바: 키 · 상태창 ─────────
with st.sidebar:
    st.header("🎤 AI 면접 코치")
    api_key = st.text_input("OpenAI 키", type="password", value=os.getenv("OPENAI_API_KEY", ""),
                            help="이 창(세션)에서만 쓰고 어디에도 저장하지 않아요.")
    st.caption(f"모델: {model_name()}")
    if "profile" in ss:
        st.subheader("상태창")
        n = min(ss.q_index + 1, coach.TOTAL_QUESTIONS)
        st.write(f"질문 **{n}/{coach.TOTAL_QUESTIONS}** · 꼬리 질문 {ss.follow_ups_used}/{coach.MAX_FOLLOW_UPS}")
        st.progress(ss.understanding / 100, text=f"면접관이 본 이해도 {ss.understanding}")
        if st.button("처음부터 다시"):
            reset()
            st.rerun()

# ───────── 시작 화면 ─────────
if "profile" not in ss:
    st.title("🎤 AI 면접 코치")
    st.write("클래스로(가상 회사) 신입 모의면접이에요. 질문 5개, 질문마다 꼬리 질문은 최대 1개예요.")
    st.button("가상 지원자 예시 채우기", on_click=fill_example)
    ss.setdefault("f_company", "클래스로")
    with st.form("start"):
        name = st.text_input("이름", key="f_name")
        job = st.selectbox("직군", ENABLED_JOBS, key="f_job")
        company = st.text_input("회사", key="f_company")
        experience = st.text_area("내 경험 (30자 이상)", key="f_experience", height=140,
                                  placeholder="해 본 일 · 한 행동 · 결과를 적어 주세요. 여기 적은 것만 사실로 다뤄요.")
        submitted = st.form_submit_button("면접 시작", type="primary")
    if submitted:
        if not name.strip() or not company.strip():
            st.warning("이름과 회사를 적어 주세요.")
        elif len(experience.strip()) < 30:
            st.warning(f"내 경험을 30자 이상 적어 주세요. (지금 {len(experience.strip())}자)")
        else:
            start({"name": name.strip(), "job": job, "company": company.strip(), "experience": experience.strip()})
            st.rerun()
    st.stop()

# ───────── 면접 화면 ─────────
st.title("🎤 면접")
for m in ss.messages:
    with st.chat_message(m["role"], avatar="🧑‍💼" if m["role"] == "assistant" else None):
        st.markdown(m["content"])

if ss.finished:
    st.success("면접이 끝났어요. 📊 평가는 다음 단계에서 열려요.")
else:
    answer = st.chat_input("답을 입력하세요")
    if answer:
        if not api_key.strip():
            st.warning("사이드바에 OpenAI 키를 넣고 다시 보내 주세요.")
            st.caption(f"보낸 답: {answer}")
        else:
            try:
                with st.spinner("면접관이 듣고 있어요…"):
                    handle_answer(api_key.strip(), answer)
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))
                st.caption(f"보낸 답: {answer}")
