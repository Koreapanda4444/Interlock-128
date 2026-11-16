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

21번 `recovery`: GF(2) 소거로 L32 역행렬을 만들고 32개 기저의 양방향 합성을 확인합니다. PRESENT 역치환과 함께 명세의 1R 식으로 k0/k3를 복구합니다. full에서 1,024키×서로 다른 평문 2개를 C로 암호화하고, 첫 쌍의 복구값을 실제 확장키와 비교한 뒤 다른 쌍의 FS 관계도 확인했습니다. 1,024키·2,048쌍 모두 일치했습니다. [결과](../research/results/recovery-full.json). 복구 대상은 첫 라운드 확장키의 64비트이며 256비트 마스터키나 전체 28라운드 키가 아닙니다.

22번 `constraints`: 2R 네 출력차분 집합과 3R 지지집합 상계를 정확 계산했습니다. full 128키×128쌍에서 2R/3R 각각 16,384쌍을 C로 검사했고 반례 0개였습니다. 3R 출력 두 번째 워드의 `0x001f001f` 10비트는 항상 0이었습니다. [결과](../research/results/constraints-full.json). 이상적 랜덤 순열의 단일 쌍 조건 만족 확률을 기록하되 관측 쌍들의 독립성이나 전라운드 보안 여유를 주장하지 않습니다. 반례가 있으면 최소 재현 입력/출력과 실패 상태를 저장합니다.

23번 `components`: 입력 16개를 전수 계산한 DDT의 비영 입력차분 행 최대 빈도는 4/16, Walsh LAT 비영 입력·출력 마스크의 최대 절댓값은 8(상관 8/16), LSB부터 좌표 차수는 2·3·3·3입니다. ANF를 다시 평가해 원래 진리표와 대조하고 DDT 행 합·Walsh Parseval 항등을 확인했습니다. 21번의 GF(2) 역행렬 helper를 재사용해 L32 rank32·양방향 기저 항등을 검증했습니다. 전체 작은 표와 역행렬은 [결과](../research/results/components-full.json)에 있습니다. 이는 부품의 정확 성질이며 전체 암호의 안전성 경계가 아닙니다.

24번 `discovery`: 명세에서 사전 고정한 full 4·8·16·28R, 입력 단일비트128개×각1,024쌍의 512조건·524,288쌍을 완료했습니다. 출력128비트 반전 횟수를 모두 계산하고 라운드마다 `abs(2*count-N)` 최대 하나를 선정했습니다. 동률은 입력비트·출력비트 오름차순입니다. 4개 선택 결과와 입력/계수 행렬 해시는 [요약](../research/results/discovery-full.json)에, 모든 65,536개 count는 build/research/discovery-full-counts.jsonl에 기록합니다. 원시 행렬에서 전역 최대와 동률 선택을 별도 재계산해 일치를 확인했습니다. discovery의 선택된 편향을 새 유의성 증거로 해석하지 않으며 다음 단계에서 다른 키·표본으로 확인합니다. holdout의 키 index1~4·각32,768쌍도 후보를 보기 전에 같은 registration에 고정했습니다.

25번 `holdout`: 24번의 후보4개를 유지하고 discovery와 다른 키 index1~4, 다른 holdout label의 새 표본으로 각32,768쌍을 확인했습니다. 16개 cohort·524,288쌍을 완료했습니다. discovery 재생성과 원시 계수 hash/전역 최대·동률/소스·실행파일 검증을 먼저 수행하며 holdout 결과로 후보를 다시 고르지 않습니다. 명시적 `--discovery-json` 캐시가 달라지면 실패하고 재실행을 요구합니다. [결과](../research/results/holdout-full.json)에 각 키의 반전 횟수·비율·Wilson95% 구간과 키4개의 단순 합산 비율을 분리해 기록했습니다.

Wilson 구간은 [NIST의 score interval 공식](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)을 사용했습니다. 경계 0/n·n/n, 대칭성, 중앙값 항등과 NIST의 반올림 예제를 확인했습니다. 16개 구간은 각각의 명목95% 구간이며 동시95% 보장을 주장하지 않습니다. 가족 단위 유의성 검정과 discovery의 선택 후 p-value는 계산하지 않습니다. 구간은 고정 생성 표본에 대한 Bernoulli 참고모형의 기술통계이며 암호 보안 강도의 구간이나 전체 키 모집단에 대한 증명이 아닙니다.

26번 최종 실행은 여섯 단계 전부 complete였으며, 기본 full 예산1,200초 중 약41.06초를 사용했습니다. [통합 기준선](../research/results/full-baseline.json)은 고정 후보와 cohort별 결과가 개별 실행과 같음을 확인한 기록입니다. 0.3초 강제 예산에서도 완료한 discovery5조건·5,120쌍을 보존한 incomplete checkpoint를 확인했습니다. 해석과 미탐색 공격군은 [security_ko.md](security_ko.md)에 정리했습니다. 27번 성능 측정은 시작하지 않았습니다.
