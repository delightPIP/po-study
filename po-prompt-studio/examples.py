"""공개용 예시 — 가상 PO 윤하늘과 가상 서비스 3개. 사람 · 서비스 · 숫자는 모두 지어낸 것.

내 예시는 my_examples.py(저장소에 안 올라감)에 MY_EXAMPLES로 두면 목록 맨 앞에 붙어요.
빈칸은 '' (프롬프트에는 '미정'으로 들어감) — 빈칸 채우기 도구를 시험하려고 일부러 남겨 둠.
"""

SERVICE_FIELDS = [
    ("me", "나 (역할 · 경력)"),
    ("name", "서비스 이름(가칭)"),
    ("customer", "주 고객"),
    ("problem", "문제 상황 (언제, 어떤 불편)"),
    ("solution", "해결 아이디어"),
    ("team", "팀"),
    ("goal", "첫 출시 목표 (언제까지, 무엇을 확인)"),
    ("rules", "이 서비스만의 지킬 것"),
]

PERSONA = "윤하늘(가상) — 웹 개발 3년 후 PO로 전환 중인 신입 PO"
TEAM_SOLO = "나 혼자, PO 겸 기획, 개발은 AI 도움"

PUBLIC_EXAMPLES = {
    "예시 · 빨래방 — 빨래톡 (가상)": {
        "me": PERSONA,
        "name": "빨래톡",
        "customer": "동네 셀프 빨래방을 쓰는 1인 가구 직장인",
        "problem": "퇴근 후 빨래방에 갔는데 세탁기 · 건조기가 다 차 있어 30분 넘게 기다리거나 그냥 돌아옴",
        "solution": "빨래방 기계가 지금 비어 있는지와 끝나는 시간을 미리 보여 줌",
        "team": TEAM_SOLO,
        "goal": "",
        "rules": "",
    },
    "예시 · 반려식물 — 물주기 (가상)": {
        "me": PERSONA,
        "name": "",
        "customer": "식물을 키우고 싶은데 자꾸 시들게 만드는 초보 식물 집사",
        "problem": "물을 언제 얼마나 줘야 하는지 몰라서, 너무 자주 주거나 잊어버림",
        "solution": "",
        "team": TEAM_SOLO,
        "goal": "",
        "rules": "식물 관리 정보는 출처 · 기준을 표시",
    },
    "예시 · 전공책 나눔 — 책다리 (가상)": {
        "me": PERSONA,
        "name": "책다리",
        "customer": "학기마다 비싼 전공책을 사야 하는 대학생",
        "problem": "한 학기만 쓰는 전공책을 새로 사기엔 비싸고, 선배 책을 구하려 해도 연락할 곳이 없음",
        "solution": "같은 학과 선후배끼리 지난 학기 전공책을 나누거나 싸게 넘기게 이어 줌",
        "team": TEAM_SOLO,
        "goal": "",
        "rules": "학번 · 연락처 같은 개인정보는 최소로",
    },
}

try:  # 로컬에만 있는 내 예시 (없으면 공개 예시만)
    from my_examples import MY_EXAMPLES
except ImportError:
    MY_EXAMPLES = {}

EXAMPLES = {**MY_EXAMPLES, **PUBLIC_EXAMPLES}
