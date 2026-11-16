# 유한 연구 실행

제품의 수식·키 도메인·28라운드·출력은 유지합니다. `CRYPTO_BUILD_RESEARCH=ON`일 때만 별도 Python 도구와 비공개 prefix 드라이버를 빌드합니다. 제품 라이브러리나 설치 패키지에 축소 라운드 진입점을 추가하지 않습니다. BUILD_TESTING=OFF인 연구 전용 빌드도 지원합니다.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCRYPTO_BUILD_RESEARCH=ON
cmake --build build --config Release
cmake --build build --config Release --target research-smoke
cmake --build build --config Release --target research-full
```

결과는 build/research 아래 JSON에 기록합니다. smoke의 기본 예산은 120초, full은 1,200초입니다. 완료한 사례를 원자적으로 checkpoint하고 시간초과 시 `incomplete`, 실행/반례/검증 실패 시 `failed`로 구분합니다. 종료 코드는 각각 complete=0, failed=1, incomplete=2입니다. 예산을 자동 연장하지 않습니다. `--budget-seconds`로 더 작은 재현 예산을 지정할 수 있습니다. CI에는 120초 이내의 smoke만 등록합니다.

`--stages`는 현재 실제 구현된 단계만 받습니다. 20번에서는 harness를 등록해 연구 도메인·LE32 필드·label 분리·반복 입력, C/Python 전체 키 일정과 28라운드 암호화·역변환을 검사합니다. smoke는 8키, full은 32키이며 이 단계의 full 완료가 아직 추가하지 않은 모든 암호분석의 완료를 뜻하지 않습니다. 21번 이후 구현된 실험을 순서대로 등록합니다.

seed는 20261109입니다. 스트림은 `Interlock-128/research || NUL || label || NUL || LE32(seed,rounds,input_bit,key_index)`를 SHAKE256으로 확장합니다. key label은 rounds/input_bit를 0으로 고정합니다. discovery와 holdout는 서로 다른 label과 키 index를 사용합니다. 고정 생성 표본의 일치를 안전성 증거로 해석하지 않습니다.

각 결과에는 실제 소스·KAT JSON·실행파일 SHA-256, 컴파일러/구성/flags, OS·아키텍처·Python·OpenSSL 버전, seed·예산·실행시간·완료 사례를 기록합니다. Python과 C가 같은 OpenSSL을 사용할 수 있으므로 독립 SHAKE 구현 검증으로 부르지 않습니다. 커밋한 작은 결과 요약과 대량 build 산출물을 구분합니다.

20번 검증은 정상 smoke/full과 연구 전용 빌드, 고정 seed 재현, C 드라이버 실패, 실제 자식 프로세스 timeout, 0초 예산 incomplete JSON, 초기화 실패 JSON을 포함합니다. 오류를 성공으로 바꾸거나 실패한 KAT를 새 출력으로 고치지 않습니다.
