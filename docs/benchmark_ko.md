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

Linux/macOS는 monotonic clock, Windows는 QPC를 사용합니다. 공유 호스트이며 affinity·CPU 주파수는 고정하지 않았습니다. 중앙값·최솟값·최댓값을 기록하고 cycle 수를 주장하지 않습니다. CI의 작은 benchmark smoke는 수치의 우열을 판정하지 않습니다. AES 참고·호환 최적화 평가는 다음 단계에서 추가합니다.
