# 독립 구현 대조

`tests/reference.py`는 규범 수식에서 작성한 Python 정수·표 S-box 구현입니다. C 코어를 호출하거나 로드하지 않습니다. `tests/vectors.json`은 명세의 고정 기대값이며 실행 중 재생성하지 않습니다. Python hashlib와 C EVP가 같은 OpenSSL을 사용할 수 있으므로 독립 SHAKE 구현 검증이라고 부르지 않습니다.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --config Release
cmake --build build --config Release --target check-differential
```

연구 옵션 기본 OFF 상태에서도 실행합니다. seed 20261109, 명세의 `Interlock-128/test` 도메인과 LE32 seed/index로 만든 1,024개 키·블록에서 전체 112워드 일정, 각 0~28라운드 출력, 각 prefix의 역변환을 비교합니다. 추가로 제품 공개 API의 전체 암호화·복호화를 같은 데이터에 대조합니다. 최초 불일치에 사례와 라운드를 표시하고 실패합니다. CTest의 `differential`과 위 target은 같은 검사를 실행합니다.

`vector_runner`는 공개 API만 사용하고 `enc`·`dec`의 28라운드만 받습니다. `prefix_runner`는 테스트 전용으로 빌드하며 제품에 설치하지 않습니다. 두 드라이버는 공백 구분 `operation rounds key_hex block_hex` 한 줄에 결과 hex 한 줄을 출력합니다. `prefix_runner`만 0~28라운드와 `keys 28 ...` 요청을 지원하며 keys 결과는 전체 448바이트 일정의 LE 직렬화입니다. JSON은 Python에서만 처리합니다. 잘못된 줄에는 `ERR`를 출력하고 전체 종료 상태를 실패로 남깁니다.

이 대조는 구현 일치 검사입니다. 차분 공격이나 안전성 증명이 아닙니다. 20번 이후 연구 실험과 구분합니다.

16번 계약 검사는 입력 길이 0/1/15/16/17/SIZE_MAX, 출력 용량 0/15/16/17의 조합을 작은 실제 할당과 경계 sentinel에서 검사합니다. 잘못된 길이·용량을 거부하기 전에 읽거나 쓰면 후속 sanitizer가 감지할 수 있도록 실제 객체 크기도 줄입니다. SIZE_MAX는 선언 길이의 거부 경로만 검사하며 해당 크기의 객체를 할당했다는 뜻이 아닙니다. ±1..15 중첩과 정확 in-place 및 인접한 분리 버퍼를 포함한 -32..32 오프셋을 검사합니다.

할당·EVP 실패 주입은 별도 `INTERLOCK_TESTING` 라이브러리에서만 수행합니다. 소거 관찰기는 아직 유효한 메모리를 `OPENSSL_cleanse` 직후, 해제 전에 확인합니다. 해제 후 읽기·이중 해제·미초기화 포인터 검사는 사용하지 않습니다. 이 관찰기는 제품 라이브러리에 포함되지 않으며 동시성 검사는 관찰기가 없는 제품 라이브러리만 링크합니다.

15번 로컬 결과: 일정 1,024개, 정방향 prefix 29,696개, 역변환 prefix 29,696개, 공개 API 2,048개 대조 모두 일치. 생성한 1,024개 `key || block` 연결의 SHA-256은 `5b8df36607cb0d0810d47f345bc47f92500a95dcd12c7cf1ab08182449e9bdd4`입니다. Linux GCC 14.2·Python 3.12.14에서 약 9.53초였으며 성능 벤치마크 수치로 쓰지 않습니다.

18번은 설치 후 prefix를 다른 위치로 옮긴 다음, `tests/consumer` 두 파일만 복사한 별도 CMake 프로젝트에서 `find_package(Interlock128 CONFIG)`와 `Interlock128::interlock`만 사용합니다. 공개 헤더로 생성→암호화→복호화→해제를 수행하고 고정 벡터를 확인합니다. 설치된 archive를 nm/dumpbin으로 검사해 테스트·prefix 진입점이 없고 네 공개 심볼이 존재하는지 확인합니다. 내부 헤더와 드라이버는 설치하지 않습니다.

Release·ASan/UBSan 빌드에서 consumer 포함 CTest 17/17을 통과했고, BUILD_TESTING=OFF 별도 제품 빌드에서도 설치·이동·별도 consumer 실행을 통과했습니다. 로컬 LSan 제외 조건은 sanitizer 문서와 같습니다. `check-consumer` target은 같은 재현 검사를 제공합니다.
