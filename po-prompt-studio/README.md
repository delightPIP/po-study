# PO 프롬프트 스튜디오

서비스 하나를 문제 발견부터 출시 후 회고까지 8단계 · 도구 21개로 따라가는 PO 전용 프롬프트 생성기.

- 사이드바에 내 서비스(상황 블록)를 채우면 모든 프롬프트 맨 앞에 붙어요. 가상 예시 3개(빨래톡 · 물주기 · 책다리)를 불러올 수 있어요
- 내 예시는 `my_examples.py`에 `MY_EXAMPLES`로 두면 로컬에서만 목록 맨 앞에 보여요 (저장소에 안 올라감)
- 단계 → 도구 → 칸 채우기 → 프롬프트 복사
- 내 OpenAI 키를 넣으면 [AI로 실행] · [⑫ 점검] · [⑰ APE로 개선] · 답을 다른 칸으로 넘기기
- 기록(.md)과 Claude 프로젝트 지침(.md) 내려받기

## 로컬 실행

```bash
cd po-prompt-studio
pip install -r requirements.txt
streamlit run app.py
```

`.env`에 `OPENAI_API_KEY`를 넣어 두면 키 칸 기본값으로 쓰여요 (선택, `.env`는 커밋 안 됨).

## 배포 — Streamlit Community Cloud

1. [share.streamlit.io](https://share.streamlit.io)에 GitHub 계정으로 로그인
2. **Create app** → 저장소 `delightPIP/po-study` · 브랜치 `main` · Main file path `po-prompt-studio/app.py`
3. App URL을 정하고 **Deploy**
4. **Secrets에는 키를 넣지 않아요.** 쓰는 사람이 사이드바에 자기 키를 넣어야 AI 버튼이 열려요
   - 모델을 바꾸고 싶을 때만 Advanced settings의 Secrets에 `OPENAI_MODEL = "모델 이름"` 한 줄

## 배포 전 확인

- [ ] `sk-` 검색 0건
- [ ] `.env`가 커밋에 없음
- [ ] 키 없이 열었을 때 AI 버튼 3개가 꺼져 있음
- [ ] 내 키로 [AI로 실행] 한 번 → 답 · [⑫ 점검] · 넘기기 동작
