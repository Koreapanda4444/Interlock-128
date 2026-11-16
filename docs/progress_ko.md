# 구현 진행표

이번 요청 범위는 **27~32번**이며, 1~26번에 이어 진행합니다. 푸시 후 인위적인 대기 없이 진행합니다.

대상: `Koreapanda4444/Interlock-128`, `main`. 원격 비어 있음과 push 권한 확인. 이전 코어 미승계.

단계별 구현·검증 후 커밋과 원격 반영. 2026-11-16 사용자 변경 지시에 따라 푸시 후 5분 정지를 해제하고 계속 진행합니다. 최종 SHA는 인계 보고에 기록.

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
| 13 | `feat: expose full-round block decryption` | 완료 | `db3791eccf36e0e6b4dcf78ae1f812ef9444d30c` / 네 KAT 복호화·양방향 in-place·입력/후방 sentinel 보존·오류 출력불변; CTest 11/11; BUILD_TESTING=OFF 제품 빌드·테스트 진입점 부재 확인
| 14 | `test: add independent reference oracle` | 완료 | `8ba87deecba68b5d7099187d8da72ff3faac0506` / 독립 Python 정수·표 S-box oracle 및 고정 JSON 벡터; 네 전체 KAT·1/4/28R KAT·116회 oracle 역변환·SHAKE KAT 일치; GCC14 fresh CTest 12/12
| 15 | `test: compare all round prefixes` | 완료 | `93062851f36d15fe01b9f91b9111266e5e8712b9` / 연구 옵션 OFF에서 1,024개 전체일정·29,696개 정방향/29,696개 역방향 prefix·공개 API2,048개 일치; 기존 CTest12/12+check-differential 통과
| 16 | `test: cover buffer and lifetime contracts` | 완료 | `774a82cf24ab9b6e21958fb957e0bba26558cf58` / 길이6×용량4 조합·±32오프셋·슬롯/키 부분겹침·6개 실패주입·해제 전 소거 확인; 제품 컨텍스트 4스레드×4096회 왕복; CTest15/15
| 17 | `test: add sanitizer and deterministic fuzz checks` | 완료 | `26b01c9357af1ac50d2feef6cf66dff556957821` / 고정seed16,384조합; Release16/16·로컬 GCC ASan/UBSan16/16 진단0; 로컬 LSan은 ptrace 차단으로 미검증, CI GCC/Clang 누수검사 ON
| 18 | `test: verify external c consumer builds` | 완료 | `eeaea3492effcf65549059861d49bb714c376eca` / 공개 CMake 패키지 설치·prefix 이동·독립 C 소비자 및 nm 심볼격리; Release/로컬 ASan·UBSan CTest17/17·제품단독 소비자 통과; CI17 GCC/Clang LSan까지 성공
| 19 | `test: audit secret-dependent code paths` | 완료 | `2f113ac0404ef1752ea44910a5fe03c9d9243821` / 소스 비밀흐름·GCC14 x86_64 O3 제품10함수 수동 검토·재현 inventory/해시/소거보존; spill 한계 명시; Release/로컬 ASan·UBSan CTest18/18
| 20 | `feat: add reproducible research harness` | 완료 | `b718dcbea78a567e65fc2219e7de80c087f5dc4d` / 연구/제품 target 분리·정확 seed 프레이밍·코드/실행파일 해시·완료/실패/timeout JSON; 기존18검사+연구2검사 통과, smoke/full 및 BUILD_TESTING=OFF 연구 빌드 검증
| 21 | `test: reproduce outer subkey recovery` | 완료 | `4b21e8b93adde16732ca60fce536569f392d55af` / GF(2) L32 역행렬·32기저 양방향 항등·역 S 검증; 1R k0/k3 64비트 복구 full1024키×2쌍·다른 평문 FS 관계 모두 일치, smoke/연구검사 통과
| 22 | `test: reproduce reduced-round differential constraints` | 완료 | `2511749fb0ccf1d9a2e09e9d477519623b3f9385` / 2R 네값·3R 지원상계/10개 강제0비트 정확계산; full128키×128쌍 각16384쌍 C 검증 반례0·smoke/연구검사 통과
| 23 | `feat: calculate exact component properties` | 완료 | `baa538a5df6ae6f4edfb092ea8eb18c1b1025e5f` / DDT/LAT/ANF 전수·행합/Parseval/진리표 재구성; 4/16·Walsh8/16·차수2,3,3,3·L32 rank32 및 기존 역행렬 항등 확인, smoke/연구검사 통과
| 24 | `feat: screen registered differential masks` | 완료 | `d9ba986c02fb541ddf40f742b4a960b8d9b62d31` / 사전등록 4/8/16/28R×입력128×1024쌍=524288쌍, 출력128계수·65536비교; 라운드별후보와동률규칙을 원시행렬로 재검산·반복결과일치, smoke/연구검사 통과
| 25 | `test: validate findings on independent holdouts` | 완료 | `340d3bbbb4eb347dc0897844bc1ab10c7f3e2861` / 고정후보4개×다른키4개×32768쌍=524288쌍 full 완료·16개 Wilson95 구간/합산비율 분리; 캐시/재선택 방지·구간경계/NIST검사 및 연구 smoke 통과
| 26 | `docs: record attack scope and unresolved questions` | 완료 | `e7a8659f856524d36a7a23f8394777429bf73ebb` / 성공한1R/2R/3R 공격·부품 exact·전체 discovery/holdout·한계/미탐색 문서화; full6단계 complete41.06초/1200초·Release/로컬 ASanUBSan22/22·제품소비자 통과, 코어/KAT 불변
| 27 | `feat: measure setup and block processing costs` | 완료 | `7365bebc249917946812fff176eedea2435c04dc` / native C 공개API11항목·최소5표본·KAT/전체길이왕복·checksum/환경/원시시간; Release23/23·샘플수 오류거부; 실제 비용경계 분리
| 28 | `feat: add aes reference measurements` | 완료 | `8119660bcd633e4f92a8a78e5bfd04f04facd85e` / AES33항목×5표본·FIPS197 정역KAT·기본/CPUcap0:0 실측; Release23/23; 추가 타이머수정/오류진단·100µs clock 회귀 통과
| 29 | `test: evaluate bit-compatible scalar optimizations` | 완료 | 실제 ANF 공통항 변형 생성·원본/후보 Release23/23 및 full6단계 동일; 순서교대3쌍×5표본·기계어차이 확인; 개선 불일관으로 제품코어 유지
| 30 | `docs: report reproducible performance results` | 대기 | — |
| 31 | `docs: finalize implementation and research handoff` | 대기 | — |
| 32 | `test: verify clean-checkout acceptance` | 대기 | — |

CI 5번 (`526221f`): Linux GCC/Clang 성공; Windows는 OpenSSL 설치 중, macOS는 러너 대기. [실행 기록](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42648381420).

CI 6번 (`68b6e1f`): Linux GCC/Clang·macOS 성공, Windows 실행 중. [실행 기록](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42649477240).

CI 5번 (`526221f`): Linux GCC·Clang, Windows MSVC x64, macOS 모두 성공 확인.

CI 12번 (`5ba9dcc`): Linux GCC·Clang 성공, Windows 실행 중, macOS 러너 대기. [실행 기록](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42655876272). 최종 13번 SHA와 CI 상태는 인계 응답에서 보고합니다.

이전 요청 종료 범위: 13번. 이번 요청에서 14~19번 독립 검증과 구현 안전성 검사를 추가합니다. 암호분석·성능·최종 인수는 20~32번 후속 범위입니다.

13번 최종 CI: Linux GCC/Clang·Windows MSVC x64·macOS 성공 확인. [기록](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42657019426).

14번 이후 로컬 재개 환경: Linux x86_64, GCC 14.2.0, Python 3.12.14, OpenSSL 3.5.7. 이전 GCC 13.3·OpenSSL 3.0.13 결과와 구분합니다.

17번 CI (`26b01c9`): Linux GCC·Clang의 Release 및 Debug ASan·UBSan·LSan(detect_leaks=1) 단계 모두 성공. macOS Release 성공, Windows 실행 중. [실행](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42733975841). 로컬 LSan 차단과 구분합니다.

19번 요청 종료 범위: 1~19번 구현·검증·원격 반영. 20~32번 연구/성능/최종 인수는 대기이며 시작하지 않습니다. 마지막 19번 자신의 SHA와 최종 CI 결과는 인계 응답에서 기록합니다.

19번 로컬 최종: Release CTest18/18, ASan·UBSan CTest18/18 통과(로컬 detect_leaks=0, LSan ptrace 제약). 대표 GCC14 산출물 10개 함수 검토; S-box 조건분기/명시 데이터 주소 없음, 컴파일러 spill 잔여 사본 한계를 기록했습니다. CI 누수 검사는 계속 detect_leaks=1입니다.

19번 최종 CI: Linux GCC·Clang, Windows MSVC x64, macOS 모두 성공 확인. [실행](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42737146398).

26번 최종 범위: full 여섯 단계 complete(약41.06초/예산1,200초), Release22/22·로컬 ASan/UBSan22/22, 제품 단독 설치 소비자 성공. 코어5개 파일 해시는19번과 동일하며 수식·도메인·라운드·KAT를 변경하지 않았습니다. 0.3초 예산의 partial checkpoint에서도 완료5조건·5,120쌍이 보존됐습니다. 27~32번은 시작하지 않았습니다.

CI 이력: 20번 macOS 작업은 cancelled(실행 단계 없음), 나머지3개 환경은 성공이었습니다. 이후21·22·23번 전체 CI는 성공했습니다. [20번](https://github.com/Koreapanda4444/Interlock-128/actions/runs/43890280445), [23번](https://github.com/Koreapanda4444/Interlock-128/actions/runs/43891830287). 마지막26번 자신의 SHA와 최종 CI는 인계 응답에서 기록합니다.

추가 수정 `fix: handle sub-resolution benchmark warmups`: 28번 macOS의 benchmark_smoke가 native exit1로 실패했고 나머지21검사는 성공했습니다. 기존 Python wrapper가 stderr를 숨겨 원인 메시지는 로그에 없었습니다. 오류를 그대로 전달하도록 고치고, 단일 untimed warmup/calibration의0시간은 허용하되 정식 표본은 반복을 늘려 반드시 양수 시간을 확보합니다. 실제 macOS 재검증 결과는 후속 기록/인계에서 보고합니다. Linux 두 compiler의28번 검사는 성공했습니다.

타이머 수정 로컬 검증: 100µs 단위로 시간을 양자화한 실제 clock shim에서 수정 전 실행파일은 nonpositive measurement interval로 실패하고 수정 후는33행×5표본 모두 양수 시간으로 완료했습니다. 일반 benchmark_smoke도 성공했습니다. 이 재현은 macOS 원인 단정이 아니라 동일한 짧은 시간 구간 실패 경로의 회귀 검사입니다.
