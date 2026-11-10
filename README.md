# Interlock-128

128비트 블록, 256비트 키, 28라운드 실험용 블록 암호의 C11 구현·독립 검증·제한된 암호분석 연구 저장소입니다.

유일한 규범 사양은 [docs/spec_ko.md](docs/spec_ko.md)입니다. 기존 구현이나 다른 암호 프로젝트의 소스는 승계하지 않습니다. 제품 API에는 전체 28라운드만 제공합니다. 축소 라운드 인터페이스는 검증·연구용으로 분리합니다.

구현 검증은 암호학적 안전성 증명이 아닙니다. 실제 기밀 보호 용도로 승인된 암호가 아닙니다. GUI, 파일 암호화, 운용모드와 AEAD는 범위에서 제외합니다.

진행 상태는 [docs/progress_ko.md](docs/progress_ko.md)에서 확인합니다. 빌드·검증 명령은 [docs/build_ko.md](docs/build_ko.md), 공개 API의 수명·오류 계약은 [docs/api_ko.md](docs/api_ko.md)를 참고합니다.

배포 라이선스는 소유자가 아직 선택하지 않았습니다. 공개 배포 전 확인해야 합니다. OpenSSL 등 의존성의 라이선스는 별도로 적용됩니다.

현재 **1~19번**까지 구현했습니다. 전체 28라운드 API, 독립 Python oracle, 1,024개 전체 prefix 대조, 계약·동시성·고정 seed 검사, sanitizer CI, 설치 패키지의 독립 C 소비자와 구현 경로 검토를 포함합니다. [검증 기록](docs/validation_ko.md), [sanitizer 결과](docs/sanitizers_ko.md), [소스·기계어 검토 범위](docs/implementation_audit_ko.md)를 구분해 확인할 수 있습니다. 20~32번의 암호분석·성능 평가·최종 인수는 후속 범위입니다.

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
