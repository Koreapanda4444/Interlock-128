# 네이티브 성능 측정

`CRYPTO_BUILD_BENCHMARKS=ON`에서 `bench` target이 공개 전체28라운드 API를 측정합니다. 연구용 축소 라운드나 내부 코어 수치가 아닙니다. Python은 실행·JSON·환경 수집만 담당하며 측정 루프는 C입니다.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCRYPTO_BUILD_RESEARCH=ON -DCRYPTO_BUILD_BENCHMARKS=ON
cmake --build build --config Release
cmake --build build --config Release --target bench
```

결과는 `build/bench/full.json`에 저장됩니다. [27번 실측](../bench/results/interlock-setup.json)은 현재 호스트에서 실행한 첫 기준선입니다. 실행 시점의 부모 Git SHA와 별개로 실제 소스·실행파일 SHA256, compiler·flags·OpenSSL·CPU·timer·원시 표본을 기록합니다.

측정별 경계:

- `key_create`: 공개 생성 API·할당·SHAKE256·448B 일정. 포인터 배열 할당과 생성 후 해제 제외.
- `key_free`: 미리 생성한 일정의 소거·해제. 생성·배열 해제 제외.
- `fresh_key_encrypt_free`: 생성→16B 공개 암호화→소거·해제 전체 비용.
- `encrypt_ready`/`decrypt_ready`: 준비된 키를 재사용해 공개 API를16B마다 호출. 검사·28라운드·공개 API의 임시 상태 소거 포함. 16B/1KiB/16KiB/1MiB는 독립 블록 반복이며 운용모드가 아닙니다.

각 행은 untimed warmup3회와 doubling calibration 후 최소5표본입니다. 기본 calibration 목표는40ms이고 키 생성/해제는 메모리 상한8,192컨텍스트로 제한하므로 모든 표본40ms 이상을 약속하지 않습니다. 실제 iterations·경과시간을 보존합니다. 입력 생성·버퍼 할당·KAT·전체 길이 왕복·측정 후 checksum·출력은 시간 구간 밖입니다. 외부 공개 호출과 결과 소비로 제거를 방지하며 LTO를 요청하지 않습니다. callback·루프·성공 반환 확인 비용은 포함됩니다.

Linux/macOS는 monotonic clock, Windows는 QPC를 사용합니다. 공유 호스트이며 affinity·CPU 주파수는 고정하지 않았습니다. 중앙값·최솟값·최댓값을 기록하고 cycle 수를 주장하지 않습니다. CI의 작은 benchmark smoke는 수치의 우열을 판정하지 않습니다.

## AES 참고 측정

[기본 dispatch 실측](../bench/results/aes-default.json)과 [x86 capability 제한 실측](../bench/results/aes-capabilities-zero.json)은 같은 프로그램·호스트·길이·표본 수를 사용합니다. `AES-256-ECB/16B-updates`는16B마다 EVP Update를 호출하며 `batch-update`는 버퍼당 한 번 호출합니다. 두 수치를 혼합하지 않습니다. OpenSSL cipher fetch와 provider 로딩은 시간 구간 밖이며 생성은 ctx 할당·방향별 키 초기화·padding off를 포함합니다. fresh는 Update·Final·free까지, ready는 Update만 측정하고 모든 ready 행 이후 Final의 출력 길이0을 확인합니다.

[FIPS197 부록 C.3](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197.pdf)의 고정 AES-256 암·복호화 벡터와 모든 길이의 왕복·측정 출력 대조를 검사합니다. [OpenSSL EVP 규약](https://docs.openssl.org/3.5/man3/EVP_EncryptInit/)에 따라 padding을0으로 설정하고16배수만 처리합니다. ECB는 독립 블록을 재기 위한 도구이며 제품에 추가하지 않습니다.

기본 실행은 OpenSSL provider의 자동 dispatch이고 실제 provider 이름·CPU capability를 JSON에 남깁니다. x86 참고 실행은 프로세스 시작 전 `OPENSSL_ia32cap=0:0`으로 AES-NI/VAES capability를 끈 조건입니다. [공식 capability 설명](https://docs.openssl.org/3.5/man3/OPENSSL_ia32cap/)과 실제 반환 벡터를 함께 기록합니다. 기본 실행에 AES-NI/VAES 사용 가능 비트가 있어도 실행 명령 경로를 tracing했다고 주장하지 않습니다. 이 제한은 SHAKE 등 다른 OpenSSL 경로에도 영향을 줄 수 있으므로 제한 실행의 Interlock 키 준비 수치를 순수한 AES 가속 효과로 부르지 않습니다.

```sh
OPENSSL_ia32cap=0:0 python3 bench/run.py --source . --driver build/interlock_bench --build-dir build --compiler-id GNU --compiler-version ACTUAL_VERSION --config Release --output build/bench/aes-capabilities-zero.json
```

위 환경변수는 x86 OpenSSL 전용 참고 조건입니다. Windows에서는 PowerShell 환경변수를 설정하고 실행파일 경로에 Release 구성을 반영하며 실제 compiler 정보를 전달합니다. AES와 동일 보안 강도가 입증됐다는 비교가 아닙니다.

## 실제 스칼라 호환 최적화 실험

[29번 평가 결과](../bench/results/scalar-evaluation.json)는 PRESENT ANF의 반복 AND 항을 `t01,t12,t03,t13,t23,t012,t013,t023`으로 공유한 실제 C 변형을 생성해 평가했습니다. 제품의 수식·키 확장·라운드 수는 고정했습니다. 후보 전체 코어는 ignored build 디렉터리에만 생성하며 완성 소스 트리에 병렬 구현을 남기지 않습니다. [실험 생성기](../bench/evaluate_scalar.py)가 변형과 실행 절차를 재현합니다. Linux의 `objcopy`로 두 cipher object의 `.text`도 비교했으며 기계어는 달랐습니다.

원본/후보 각각 Release23/23(고정 KAT·1,024개 모든 prefix 포함)와 여섯 단계 연구 full이 통과했습니다. full의 정확 계산·복구·구별자·discovery 계수·holdout cohort 결과가 동일했습니다. 연구는 각각 약30.61초/30.50초에 완료됐으며 이 시간은 처리량 비교가 아닙니다.

| 쌍 | 순서 | 1MiB 암호화 원본시간/후보시간 | 1MiB 복호화 원본시간/후보시간 |
| ---: | --- | ---: | ---: |
| 1 | 원본→후보 | 1.073 | 1.029 |
| 2 | 후보→원본 | 1.039 | 0.659 |
| 3 | 원본→후보 | 1.141 | 1.222 |

비율1보다 크면 후보가 빨랐습니다. 매 실행은 최소5표본이고 세 쌍의 순서를 바꿨습니다. 암·복호화의 모든 쌍에서 최소5% 감소해야 고려한다는 기준을 충족하지 않아 **제품 코어를 유지**합니다. 특히 두 번째 복호화는 오히려 느렸습니다. 이 공유 호스트 실험 하나로 다른 CPU·compiler에서의 개선 가능성을 부정하지 않습니다. 평가 수치는 타이머 진단 수정 전28번 소스를 기준으로 했고 그 수정은 단일 untimed warmup의0시간 허용·오류 표시를 다루며 암호 연산을 바꾸지 않았습니다.

```sh
python3 bench/evaluate_scalar.py --source . --work build/scalar-rerun --cmake /actual/path/to/cmake --output build/scalar-rerun.json
```

평가기는 새 경로만 사용하고 로그·원시 표본을 남깁니다. Linux GNU 도구로 구현한 이 실험 생성기를 Windows/macOS에서 검증했다고 표시하지 않습니다. 자동으로 제품 소스를 교체하지 않습니다.
