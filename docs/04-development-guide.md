# 04. 개발 가이드

## 1) 운영 원칙

- 문서 우선: 구현 전 `01/02/03/06` 합의
- 단계 우선: 0 -> 1 -> 2 -> 3 -> 4 순서 준수
- 품질 우선: 테스트 게이트 미통과 시 단계 종료 불가
- 동기화 우선: 코드 변경 시 문서/테스트 동시 갱신
- 시작 방식: 0단계는 **AI로 초기 틀 생성 후 시작**

## 2) 기본 개발 흐름

1. Interface First 방식으로 **AI로 초기 틀 생성 후 시작**(API/폴더/테스트 템플릿)
2. 팀이 초안 검토 후 수정사항 확정
3. 해당 단계 전용 AI 초기틀 추가 생성(1~4단계 반복)
4. 파트별 구현 진행(코드 + 테스트 동시 작성)
5. Unit/Integration/Failure 검증
6. 단계 4에서 Load 검증 후 게이트 판정

## 3) 브랜치/커밋 규칙

- 브랜치: `feature/<name>`, `fix/<name>`, `docs/<name>`, `test/<name>`, `chore/<name>`
- 로컬 명령:
  - `uv venv`
  - `.venv\\Scripts\\activate`
  - `uv pip install -r requirements.txt`
  - `pytest -q`
  - `locust -f scripts/load_test.py` (또는 `k6 run scripts/load_test.js`)
  - (대안) `python -m venv .venv && pip install -r requirements.txt`

## 4) 4인 협업 역할 분담(단순 4분할)

| 파트 | 책임 | 완료 기준 |
| --- | --- | --- |
| 파트1 | API/검증 + 해당 테스트 | API 계약 테스트 통과 |
| 파트2 | 핵심 KV + 해당 테스트 | set/get/del/exists 테스트 통과 |
| 파트3 | TTL/무효화 + 해당 테스트 | expire/ttl/persist/invalidate 테스트 통과 |
| 파트4 | CI/CD/품질게이트/문서 | 단계 리포트와 docs 동기화 완료 |

원칙:
- 코드 작성자와 테스트 작성자는 분리하지 않는다.
- 파트4는 테스트 대행이 아니라 자동화 파이프라인/품질게이트를 운영한다.

## 5) 0~4단계 실행 로드맵

| 단계 | 실행 초점 | 성공 기준 | 리스크 | 완료 조건 |
| --- | --- | --- | --- | --- |
| 0 | AI 초기 틀 + Docker CI/CD 골격 생성 | 초안 품질 검토 완료 | 초안 품질 편차 | 수정 목록 합의, 파이프라인 동작 확인 |
| 1 | 핵심 KV 구현 | 계약 기반 동작 일치 | 입력 검증 누락 | 단계 1 테스트 통과 |
| 2 | TTL 기능 구현 | 시간 경계 케이스 안정 | 플래키 테스트 | TTL 실패 시나리오 통과 |
| 3 | 무효화/운영성 | 범위 삭제 안전성 확보 | 과삭제/과소삭제 | 통합+장애 시나리오 통과 |
| 4 | 통합/성능/릴리스 | 성능 기준 충족 | 병목 미확인 | 회귀+부하 검증 완료 |

## 5-1) CI/CD (Docker + EC2) 최소 구성

- CI: `pytest`, 정적 검사, Docker 이미지 빌드
- CD: 이미지 레지스트리 push 후 EC2에서 `docker compose up -d`
- 배포 완료 기준: `/v1/health` 응답 정상

## 6) 리뷰 체크리스트

- API 계약/오류 규칙 위반 여부
- Unit/Integration/Failure/Load 테스트 누락 여부
- 단계 범위 초과 구현 여부
- 리스크 대응 및 후속 액션 기록 여부

## 7) 단계 게이트 산출물

- 완료 기능 목록
- 테스트 결과(Unit/Integration/Failure/Load)
- 잔여 리스크 및 완화 계획
- 다음 단계 진입 가능 여부
