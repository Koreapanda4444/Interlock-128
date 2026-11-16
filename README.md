# Interlock-128

128비트 블록, 256비트 키, 28라운드 실험용 블록 암호의 C11 구현·독립 검증·제한된 암호분석 연구 저장소입니다.

유일한 규범 사양은 [docs/spec_ko.md](docs/spec_ko.md)입니다. 기존 구현이나 다른 암호 프로젝트의 소스는 승계하지 않습니다. 제품 API에는 전체 28라운드만 제공합니다. 축소 라운드 인터페이스는 검증·연구용으로 분리합니다.

구현 검증은 암호학적 안전성 증명이 아닙니다. 실제 기밀 보호 용도로 승인된 암호가 아닙니다. GUI, 파일 암호화, 운용모드와 AEAD는 범위에서 제외합니다.

진행 상태는 [docs/progress_ko.md](docs/progress_ko.md)에서 확인합니다. 빌드·검증 명령은 [docs/build_ko.md](docs/build_ko.md), 공개 API의 수명·오류 계약은 [docs/api_ko.md](docs/api_ko.md)를 참고합니다.

배포 라이선스는 소유자가 아직 선택하지 않았습니다. 공개 배포 전 확인해야 합니다. OpenSSL 등 의존성의 라이선스는 별도로 적용됩니다.

현재 **1~31번**을 완료했고 마지막 clean-checkout 인수를 진행합니다. 전체28라운드 공개 API, 독립 Python 대조, 메모리·실패·동시성 검사, 제한된 암호분석, 네이티브 비용 측정과 AES 참고 비교를 제공합니다. 실제 스칼라 최적화 후보는 검증했지만 효과가 일관되지 않아 기존 코어를 유지했습니다.

- [빌드·전체 재현](docs/build_ko.md), [API 계약](docs/api_ko.md), [독립 검증](docs/validation_ko.md), [sanitizer 범위](docs/sanitizers_ko.md)
- [연구 실행](docs/research_ko.md), [공격 결과와 한계](docs/security_ko.md), [소스·기계어 검토](docs/implementation_audit_ko.md)
- [실측표·재현·최적화 평가](docs/benchmark_ko.md), [인계와 후속 검토](docs/handoff_ko.md), [계획별 SHA](docs/progress_ko.md)

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCRYPTO_BUILD_RESEARCH=ON -DCRYPTO_BUILD_BENCHMARKS=ON
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
cmake --build build --config Release --target research-full
cmake --build build --config Release --target bench
```

결과 JSON과 대량 원시 표본은 build 아래에 생성합니다. 선별한 재현 기록은 `research/results/`, `bench/results/`에 있습니다. 기존 ZIP이나 다른 대화 없이 이 저장소와 실제 설치된 의존성만으로 시작할 수 있습니다.

```c
#include <interlock.h>
#include <string.h>
int main(void) {
    uint8_t key[32] = {0}, plaintext[16] = {0}, ciphertext[16], recovered[16];
    interlock_key_ctx *ctx = NULL;
    interlock_status status = interlock_key_ctx_create(&ctx, key, sizeof(key));
    if (status != INTERLOCK_OK) return 1;
    status = interlock_encrypt_block(ctx, plaintext, sizeof(plaintext), ciphertext, sizeof(ciphertext));
    if (status == INTERLOCK_OK)
        status = interlock_decrypt_block(ctx, ciphertext, sizeof(ciphertext), recovered, sizeof(recovered));
    interlock_key_ctx_free(ctx);
    ctx = NULL;
    return status != INTERLOCK_OK || memcmp(plaintext, recovered, sizeof(plaintext)) != 0;
}
```
