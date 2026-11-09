# 구현 진행표

대상: `Koreapanda4444/Interlock-128`, `main`. 원격 비어 있음과 push 권한 확인. 이전 코어 미승계.

단계별 구현·검증 후 커밋과 원격 반영. 원격 반영 완료부터 다음 단계 작업 시작까지 최소 300초 정지. 최종 SHA는 인계 보고에 기록.

| 번호 | 제목 | 상태 | 완료 SHA / 검증 |
| ---: | --- | --- | --- |
| 1 | `docs: define clean-room implementation scope` | 완료 | `35ea2194af3673530ffbbc7a80d55c77bbdb1706` / 규범 사양·32개 계획 반영; README·진행표는 2번과 반영 |
| 2 | `feat: configure portable c11 build` | 완료 | `8682d0dcdaf07ad42d703194df80ea7f9a5c3364` / GCC 13.3, OpenSSL 3.0.13, CMake 4.4.4; fresh build·CTest 1/1 |
| 3 | `feat: add defined word and buffer operations` | 완료 | `151d56a5aee5e0b58afa84552d75c3354f9a9dad` / LE 비정렬·sentinel, 0/1/31/32 회전, 범위 overflow 및 ±1..15 중첩; CTest 2/2
| 4 | `feat: add verified shake256 adapter` | 완료 | `2871682f80708c0215c3aa92be18d296181748a5` / SHAKE256 빈 입력64B 고정 KAT, 448B 단일 final, 분할 update 일치; 할당·EVP 5개 실패지점 출력 보존; CTest 3/3
| 5 | `test: establish cross-platform build checks` | 완료 | `526221f6ba081fcd6b1807a3c12c92ed2183a876` / Linux GCC/Clang·Windows MSVC x64·macOS CI 설정; YAML 검사·fresh GCC build/CTest 3/3; 원격 실행 상태는 아래 기록
| 6 | `feat: implement constant-time nibble substitution` | 완료 | S-box Boolean ANF, 16입력×8위치×4배경 전수 대조·인접 니블 보존; CTest 4/4
| 7 | `feat: implement linear and nonlinear mixing` | 대기 | — |
| 8 | `feat: implement ordered forward rounds` | 대기 | — |
| 9 | `feat: implement reverse round transitions` | 대기 | — |
| 10 | `feat: expand complete round key schedules` | 대기 | — |
| 11 | `feat: add immutable key contexts` | 대기 | — |
| 12 | `feat: expose full-round block encryption` | 대기 | — |
| 13 | `feat: expose full-round block decryption` | 대기 | — |
| 14 | `test: add independent reference oracle` | 대기 | — |
| 15 | `test: compare all round prefixes` | 대기 | — |
| 16 | `test: cover buffer and lifetime contracts` | 대기 | — |
| 17 | `test: add sanitizer and deterministic fuzz checks` | 대기 | — |
| 18 | `test: verify external c consumer builds` | 대기 | — |
| 19 | `test: audit secret-dependent code paths` | 대기 | — |
| 20 | `feat: add reproducible research harness` | 대기 | — |
| 21 | `test: reproduce outer subkey recovery` | 대기 | — |
| 22 | `test: reproduce reduced-round differential constraints` | 대기 | — |
| 23 | `feat: calculate exact component properties` | 대기 | — |
| 24 | `feat: screen registered differential masks` | 대기 | — |
| 25 | `test: validate findings on independent holdouts` | 대기 | — |
| 26 | `docs: record attack scope and unresolved questions` | 대기 | — |
| 27 | `feat: measure setup and block processing costs` | 대기 | — |
| 28 | `feat: add aes reference measurements` | 대기 | — |
| 29 | `test: evaluate bit-compatible scalar optimizations` | 대기 | — |
| 30 | `docs: report reproducible performance results` | 대기 | — |
| 31 | `docs: finalize implementation and research handoff` | 대기 | — |
| 32 | `test: verify clean-checkout acceptance` | 대기 | — |

CI 5번 (`526221f`): Linux GCC/Clang 성공; Windows는 OpenSSL 설치 중, macOS는 러너 대기. [실행 기록](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42648381420).
