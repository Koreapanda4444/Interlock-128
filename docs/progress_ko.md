# 구현 진행표

이번 요청 범위는 **1~13번**이며, 14~32번은 후속 작업으로 남깁니다.

대상: `Koreapanda4444/Interlock-128`, `main`. 원격 비어 있음과 push 권한 확인. 이전 코어 미승계.

단계별 구현·검증 후 커밋과 원격 반영. 원격 반영 완료부터 다음 단계 작업 시작까지 최소 300초 정지. 최종 SHA는 인계 보고에 기록.

| 번호 | 제목 | 상태 | 완료 SHA / 검증 |
| ---: | --- | --- | --- |
| 1 | `docs: define clean-room implementation scope` | 완료 | `35ea2194af3673530ffbbc7a80d55c77bbdb1706` / 규범 사양·32개 계획 반영; README·진행표는 2번과 반영 |
| 2 | `feat: configure portable c11 build` | 완료 | `8682d0dcdaf07ad42d703194df80ea7f9a5c3364` / GCC 13.3, OpenSSL 3.0.13, CMake 4.4.4; fresh build·CTest 1/1 |
| 3 | `feat: add defined word and buffer operations` | 완료 | `151d56a5aee5e0b58afa84552d75c3354f9a9dad` / LE 비정렬·sentinel, 0/1/31/32 회전, 범위 overflow 및 ±1..15 중첩; CTest 2/2
| 4 | `feat: add verified shake256 adapter` | 완료 | `2871682f80708c0215c3aa92be18d296181748a5` / SHAKE256 빈 입력64B 고정 KAT, 448B 단일 final, 분할 update 일치; 할당·EVP 5개 실패지점 출력 보존; CTest 3/3
| 5 | `test: establish cross-platform build checks` | 완료 | `526221f6ba081fcd6b1807a3c12c92ed2183a876` / Linux GCC/Clang·Windows MSVC x64·macOS CI 설정; YAML 검사·fresh GCC build/CTest 3/3; 원격 실행 상태는 아래 기록
| 6 | `feat: implement constant-time nibble substitution` | 완료 | `68b6e1f7b578f3e823fc3d2023966f76842849e9` / S-box Boolean ANF, 16입력×8위치×4배경 전수 대조·인접 니블 보존; CTest 4/4
| 7 | `feat: implement linear and nonlinear mixing` | 완료 | `631cfcf3b7ba90f920c0a89ef55937ac5d58b974` / L32/FS/FM 독립 C 기준식, 단일비트·최댓값·carry 경계 42×42 및 고정 1,024쌍 대조; CTest 5/5
| 8 | `feat: implement ordered forward rounds` | 완료 | `6e2250253a661e0b3c8391d2bc1786714e0ed20a` / 순서 의존 XOR 갱신과 회전·재배열, 0블록·첫4서브키 1R KAT 및 재배열 전 4워드 일치; CTest 6/6
| 9 | `feat: implement reverse round transitions` | 완료 | `f8b0bb4e25f4a0e6b471c5ac26f47e11837b473a` / 역회전·역갱신; 4,096개 상태·서브키의 양방향 1R 왕복과 별도 기준식 일치; CTest 7/7
| 10 | `feat: expand complete round key schedules` | 완료 | `a211de0f77ea4505de38f5962dc0389ef5cf73a3` / 448B 전체 일정·LE32·NUL 하나 확인, NUL 누락/추가 구분, 첫4서브키와 1R/4R/28R KAT·역변환·실패 출력보존; CTest 8/8
| 11 | `feat: add immutable key contexts` | 완료 | `58575750dbc99d89f26b08823ee09f9d6ffdcaaf` / opaque 컨텍스트 생성·불변 일정·소거/해제; 원본 키 변경 독립성, 슬롯/키 중첩·기존 슬롯 보존, malloc/EVP 6개 실패경로; CTest 9/9
| 12 | `feat: expose full-round block encryption` | 완료 | `5ba9dcc39a68f81ff7fa1422815f847b3d24b18a` / 전체28R 공개 암호화; 네 KAT, 비정렬·exact in-place·경계 sentinel, 길이/용량/NULL/±1..15 겹침 오류와 출력 보존; CTest 10/10
| 13 | `feat: expose full-round block decryption` | 완료 | 네 KAT 복호화·양방향 in-place·입력/후방 sentinel 보존·오류 출력불변; CTest 11/11; BUILD_TESTING=OFF 제품 빌드·테스트 진입점 부재 확인
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

CI 6번 (`68b6e1f`): Linux GCC/Clang·macOS 성공, Windows 실행 중. [실행 기록](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42649477240).

CI 5번 (`526221f`): Linux GCC·Clang, Windows MSVC x64, macOS 모두 성공 확인.

CI 12번 (`5ba9dcc`): Linux GCC·Clang 성공, Windows 실행 중, macOS 러너 대기. [실행 기록](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42655876272). 최종 13번 SHA와 CI 상태는 인계 응답에서 보고합니다.

요청 종료 범위: 13번. 14~32번은 미구현이며, 독립 oracle·전체 prefix 대조·sanitizer·암호분석·성능·최종 인수 완료로 해석하지 않습니다.
