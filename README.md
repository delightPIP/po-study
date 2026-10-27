# PO 공부 — 프롬프트 스튜디오 · 면접 코치

신입 PO 준비용 Streamlit 서비스 두 개를 모은 저장소예요.

| 폴더 | 무엇 | 상태 |
|---|---|---|
| [`po-prompt-studio/`](po-prompt-studio/) | 서비스 하나를 문제 발견부터 회고까지 8단계 · 도구 21개로 따라가는 PO 프롬프트 생성기 | 배포 가능 |
| [`d10-interview/`](d10-interview/) | PO 모의면접 코치 — 설계초안 · 질문 은행 · NCS 기반 예시 답변 | 설계 단계 (앱 코드 전) |

## 실행 · 배포

- 로컬: 각 폴더로 들어가서 `pip install -r requirements.txt` → `streamlit run app.py`
- Streamlit Community Cloud: 저장소 `delightPIP/po-study` · 브랜치 `main` · Main file path는 `po-prompt-studio/app.py` 처럼 **폴더까지** 적어요
- OpenAI 키는 저장소 · Secrets에 넣지 않아요. 쓰는 사람이 화면에 자기 키를 넣어요

## 예시 데이터

예시 서비스와 면접 지원자는 모두 가상이에요. 실제 인물 · 회사와 관계없어요.
내 실제 정보는 `.env` · `my_examples.py` · `*.local.md` 에만 두고, 이 파일들은 커밋되지 않아요.
