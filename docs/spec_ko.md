# Interlock-128 신규 개발 명세와 커밋 계획

문서 개정: **2.0 / 2026-11-09**. 문서 개정 번호이며 암호 알고리즘을 바꾼 버전이 아니다.

신규 저장소 목표: **`Koreapanda4444/Interlock-128`**. 새 Work에서 이 파일 하나를 첨부해 시작한다. 이 주소의 생성·접근 권한·현재 상태를 확인했다는 뜻은 아니다.

## 1. 실행 범위와 시작 조건

128비트 블록·256비트 키·28라운드 Interlock을 C11로 처음부터 구현한다. 결과물은 블록 암호 라이브러리, 독립 검증 도구, 제한된 암호분석 실험과 벤치마크다. GUI, 서버, 파일 암호화 앱, 패딩·운용모드, AEAD, 언어 바인딩은 만들지 않는다. `128`은 블록 길이이며 검증된 보안 강도가 아니다.

- **새 작업 디렉터리와 새 Git 이력**에서 시작한다. 옛 레포·소스·커밋을 clone/copy/cherry-pick하거나 이전 Work 작업을 이어받지 않는다. 기존 저장소를 수정·삭제하거나 강제 푸시하지 않는다.
- 아래 수식, API, 벡터, 연구 절차와 커밋 계획이 개발 기준이다. 원본 ZIP·감사 ZIP·다른 채팅·다른 두 암호의 문서는 필수 입력이 아니다.
- 지정 신규 원격이 비어 있으면 `main`에서 시작한다. README·LICENSE 등 초기 파일만 있으면 읽고 보존한다. 실제 구현이 이미 있거나 대상이 불명확하면 덮어쓰지 않고 확인한다.
- 원격이 없거나 권한이 부족해도 가능한 로컬 구현·테스트·커밋은 진행한다. 원격 작업은 주소와 권한 확인 후 수행하며 권한을 우회하지 않는다. 미푸시를 푸시 완료로 보고하지 않는다.
- **사전 계획은 32커밋**이다. 사용자가 N번까지 요청하면 그 범위까지, 별도 범위가 없으면 1번부터 순서대로 가능한 범위까지 구현·검증·커밋·푸시한다. 계획 설명만 하고 끝내지 않는다.
- 이번 범위에서 수식·키 도메인·라운드 수·출력은 고정이다. 문제를 찾으면 최소 재현과 영향·수정안을 기록한다. 사용자 승인 전 알고리즘을 바꾸거나 실패한 KAT를 코드 출력에 맞춰 고치지 않는다.

기능 구현, 구현 안전성 검사, 성능, 암호학적 안전성은 별도 판정한다. 마지막 단계의 목표는 **재현 가능한 연구 기준선**이지 실제 기밀 보호의 승인이나 모든 공격에 대한 안전성 증명이 아니다.

## 2. 세 프로젝트 공통 개발 규칙

### 2.1 기술 선택

| 항목 | 확정 기준 |
| --- | --- |
| 제품 코어 | C11, 고정폭 부호 없는 정수, 8비트 바이트인 지원 플랫폼 |
| 빌드·테스트 | CMake 3.20 이상, CTest. 별도 Makefile 빌드 체계를 중복 운영하지 않음 |
| SHAKE256 | OpenSSL 3.x `libcrypto`의 EVP XOF API. SHAKE를 자체 재구현하지 않음 |
| 독립 검증 | Python 3.11 이상 표준 라이브러리. `hashlib.shake_256` 사용 |
| 검증 플랫폼 | Linux GCC·Clang, Windows MSVC x64, macOS AppleClang. 실제 실행한 OS·아키텍처·버전만 검증 완료로 기재 |
| 초기 제외 | SIMD·어셈블리·GPU, 복잡한 플러그인/할당기 프레임워크, 추가 암호 모드 |

Python과 C의 암호 코어를 따로 작성한다. Python `hashlib`도 OpenSSL을 사용할 수 있으므로 이를 서로 독립적인 SHAKE 구현 검증이라고 부르지 않는다. SHAKE 어댑터에는 별도의 고정 KAT를 둔다.

### 2.2 저장소 구조

세 프로젝트의 최상위 디렉터리는 `include/`, `src/`, `tests/`, `research/`, `bench/`, `docs/`, `.github/workflows/`로 통일한다. 암호별 실제 모듈 수는 달라도 된다.

| 경로 | 용도 |
| --- | --- |
| `include/interlock.h` | 전체 라운드 공개 API만 |
| `src/interlock.c` | 워드 연산, S-box, FS/FM, 정·역라운드 및 블록 처리 |
| `src/interlock_key.c` | 키 스케줄, opaque 컨텍스트 생성·소거·해제 |
| `src/support.c`, `src/internal.h` | SHAKE 어댑터, 내부 연산·버퍼 검사. 공개 헤더가 아님 |
| `tests/test_*.c` | 실제 KAT·오류·메모리·왕복 테스트 |
| `tests/vectors.json`, `tests/reference.py` | 고정 벡터와 독립 Python oracle |
| `tests/vector_runner.c` | 검증용 C 입출력 드라이버 |
| `tests/consumer/` | 공개 헤더와 빌드된 라이브러리만 사용하는 작은 C 소비자 |
| `research/` | 축소 라운드 공격, 정확 계산, 유한 통계 실험 |
| `research/results/` | 실행 조건과 요약을 포함한 선별된 작은 JSON 결과 |
| `bench/` | 네이티브 C 측정 및 결과 요약 도구 |
| `docs/spec_ko.md` | 이 문서에서 옮긴 유일한 현재 규범 사양 |
| `docs/api_ko.md` | API 수명·오류·버퍼 계약 |
| `docs/security_ko.md` | 공격 모델, 성공 공격, 한계·미해결 |
| `docs/benchmark_ko.md` | 실제 측정 조건·결과 |
| `docs/progress_ko.md` | 계획 번호, 완료 SHA, 검증, 원격·CI 상태 |
| `CMakeLists.txt`, `README.md`, `.gitignore` | 빌드·진입 안내·생성물 제외 |
| `.github/workflows/ci.yml` | 실제 구현된 검사와 플랫폼 빌드 |

각 파일은 담당 커밋에서 실제 내용이 생길 때 만든다. 빈 폴더·성공 반환 stub·중복 명세·과거 코어 복제본·`legacy/`는 만들지 않는다. 바이너리·캐시·대량 원시 표본·임시 로그는 `build/` 아래에 두고 커밋하지 않는다. 법적 배포 라이선스는 소유자가 선택한 기존 지시가 없으면 임의로 확정하지 않고, 공개 배포 전 확인 항목으로 남긴다. 의존성의 라이선스 고지는 보존한다.

### 2.3 커밋·푸시 규칙

- 아래 표의 **영어 제목 그대로** 커밋한다. 접두어는 `feat:`, `fix:`, `test:`, `docs:`만 사용한다.
- 번호는 이 문서와 진행표에서만 사용한다. 실제 커밋 제목에 `IN-001`, `CR-002`, `DU-003`, `Commit 1`, `Phase 2`를 넣지 않는다.
- 각 커밋은 빌드 가능한 하나의 작업 단위와 관련 검증을 포함한다. 기능 코드와 그 기능을 확인하는 최소 테스트를 분리해 고장 난 중간 상태를 커밋하지 않는다.
- 작업 전 기준 상태 확인 → 구현 → 해당 단계의 로컬 검사 → 커밋 → 가능한 푸시 → 원격 CI 확인 순서다. CI가 코드 때문에 실패하면 다음 기능보다 수정을 우선한다. 환경·권한 장애는 구현 실패와 구분한다.
- 오류 수정 때문에 추가 커밋이 필요하면 구체적인 `fix:` 제목으로 남기고 진행표에 기록한다. 계획 개수에 맞추려고 빈 커밋을 만들거나 이력을 억지로 쪼개지 않는다.
- 로컬 테스트, 로컬 커밋, 푸시, CI 통과를 각각 보고한다. 계획 번호와 실제 SHA를 대응시키되 마지막 커밋은 자기 SHA를 문서에 쓰려고 다시 커밋하지 말고 인계 보고에 기록한다.

## 3. 규범 알고리즘

### 3.1 데이터와 표기

키는 정확히 32바이트, 블록은 정확히 16바이트다. 입력 블록을 차례로 LE32로 읽어 상태 `(a,b,c,d)`를 만든다. 출력도 이 순서로 LE32 직렬화한다. 덧셈은 `mod 2^32`, `^`는 XOR, `&`는 비트 AND다. `ROL32`·`ROR32`는 32비트 순환회전이다. 일반 회전 helper는 0·32도 정의된 결과를 내도록 구현하며 폭만큼 shift하지 않는다.

PRESENT S-box는 다음 16개 값이다.

```text
S = [12,5,6,11,9,0,10,13,3,14,15,8,4,7,1,2]
S_inverse = [5,14,15,8,12,1,2,13,11,4,6,3,0,7,9,10]
```

`S(x)`는 32비트의 8개 니블 각각에 같은 치환을 적용한 워드다. Python oracle에서는 표를 써도 되지만 제품 C에서는 비밀값으로 표를 인덱싱하지 않고 고정 Boolean 식 또는 같은 성질의 검증 가능한 구현을 사용한다.

### 3.2 혼합 함수

```text
L32(x) = x ^ ROL32(x,3) ^ ROL32(x,17)

FS(x,k):
    return L32(S(x ^ k))

FM(x,k):
    y = S(x ^ k)
    u = (y + ROL32(k,9)) mod 2^32
    v = ROL32(y ^ k,7)
    w = ROL32((u + v) mod 2^32,11) ^ ROL32(y & ROL32(k,3),19)
    z = S(w ^ ROL32(k,13))
    return L32(z)
```

### 3.3 키 확장

```text
input = ASCII("Interlock-128/roundkeys") || 0x00 || key[32]
stream = SHAKE256(input, 448 bytes)
round_key[r][j] = LE32(stream[16*r + 4*j : 16*r + 4*j + 4])
r = 0..27; j = 0..3
```

문자열 뒤 NUL은 정확히 1바이트다. C `sizeof`에 따른 암묵 NUL과 명시 NUL을 중복 추가하지 않는다. SHAKE 출력은 448바이트 한 번에 요청하고 성공 반환을 확인한다. 축소 라운드도 같은 112개 워드의 prefix를 사용한다. 키 길이·출력 길이·도메인은 보안 강도 주장이 아니라 형식 정의다.

### 3.4 암호화와 복호화

각 라운드 `r=0..27`에서 `(k0,k1,k2,k3)=round_key[r]`를 사용한다. **네 XOR는 아래 순서대로** 실행한다.

```text
a ^= FS(b,k0)
c ^= FM(d,k1)
b ^= FM(c,k2)       # 갱신한 c를 사용
d ^= FS(a,k3)       # 갱신한 a를 사용
(a,b,c,d) = (ROL32(c,5), ROL32(a,13), ROL32(d,21), ROL32(b,27))
```

마지막 라운드에도 재배열·회전을 수행한다. 추가 whitening·마지막 swap은 없다.

복호화는 `r=27..0` 순서다. 현재 워드를 `(o0,o1,o2,o3)`라 하면:

```text
c = ROR32(o0,5)
a = ROR32(o1,13)
d = ROR32(o2,21)
b = ROR32(o3,27)
d ^= FS(a,k3)
b ^= FM(c,k2)
c ^= FM(d,k1)
a ^= FS(b,k0)
state = (a,b,c,d)
```

라운드 전체의 가역성에 FM 역함수는 필요하지 않다. 검증용 0라운드는 항등이고 1..28은 앞부분 라운드다. **제품 공개 API에는 라운드 수 인자를 넣지 않는다.** 축소 라운드 진입점·중간 상태 노출은 별도 비공개 테스트/연구 target에서만 빌드하며 제품 라이브러리에는 포함하지 않는다. `BUILD_TESTING=ON`만으로 0..28라운드 검증 드라이버를 빌드할 수 있어야 하며, 이 경로는 `CRYPTO_BUILD_RESEARCH` 옵션과 독립적이다.

## 4. 공개 C API와 실패 계약

`include/interlock.h`는 `<stddef.h>`, `<stdint.h>`와 다음 계약을 제공한다. 공개 헤더에서 OpenSSL 내부 타입을 노출하지 않는다. include guard와 C++ 소비자를 위한 조건부 `extern "C"` guard를 둔다.

```c
#define INTERLOCK_KEY_BYTES 32u
#define INTERLOCK_BLOCK_BYTES 16u

typedef struct interlock_key_ctx interlock_key_ctx;

typedef enum {
    INTERLOCK_OK = 0,
    INTERLOCK_EINVAL = 1,
    INTERLOCK_ELENGTH = 2,
    INTERLOCK_ECAPACITY = 3,
    INTERLOCK_EOVERLAP = 4,
    INTERLOCK_ENOMEM = 5,
    INTERLOCK_ECRYPTO = 6
} interlock_status;

interlock_status interlock_key_ctx_create(
    interlock_key_ctx **out_ctx, const uint8_t *key, size_t key_len);
void interlock_key_ctx_free(interlock_key_ctx *ctx);

interlock_status interlock_encrypt_block(
    const interlock_key_ctx *ctx,
    const uint8_t *input, size_t input_len,
    uint8_t *output, size_t output_capacity);
interlock_status interlock_decrypt_block(
    const interlock_key_ctx *ctx,
    const uint8_t *input, size_t input_len,
    uint8_t *output, size_t output_capacity);
```

### 4.1 컨텍스트와 소유권

- `interlock_key_ctx_create`에서 `out_ctx`와 `key`는 비NULL이며 `key_len==32`여야 한다. `out_ctx`는 초기화된 포인터 변수의 주소이고 `*out_ctx==NULL`을 전제로 한다. 기존 값이 비NULL이면 덮어쓰지 않고 `INTERLOCK_EINVAL`을 반환한다.
- 실패하면 `*out_ctx`를 변경하지 않는다. 정상 전제에서 실패 후에도 NULL이다. 성공한 뒤에만 새 컨텍스트 주소를 기록한다. `out_ctx` 슬롯과 키 입력의 메모리 범위는 겹치면 안 되며 해당 중첩은 검사한다.
- 컨텍스트는 112개 라운드키를 소유하고 생성 후 불변이다. 원본 키는 생성 후 보관할 필요가 없다. 호출자는 자신의 키 버퍼를 소거할 책임을 가진다.
- `interlock_key_ctx_free(NULL)`은 no-op이다. 해제 전에 라이브러리가 보유한 키 일정을 소거한다. 호출자는 해제 뒤 포인터를 NULL로 바꾸며, 해제 후 사용·이중 해제는 호출자 오류다.
- 읽기 전용 컨텍스트를 여러 스레드에서 서로 겹치지 않는 입출력에 재사용할 수 있게 전역 가변 scratch를 두지 않는다. 실행 중 해제와 동시 호출의 동기화는 호출자 책임이다.

### 4.2 블록 처리

- `ctx`, `input`, `output`은 모두 비NULL. `input_len==16`, `output_capacity>=16`을 검사한다. 성공하면 처음 16바이트만 쓰며 뒤쪽 용량은 보존한다.
- `input==output`인 정확한 in-place를 지원한다. 서로 다른 시작 주소의 입출력 16바이트 범위가 겹치면 `INTERLOCK_EOVERLAP`. 길이·용량·중첩 검사 후 로컬 워드/임시 16바이트에서 계산하고 마지막에 출력한다.
- **오류 반환 시 호출자 데이터 출력 버퍼는 전혀 바꾸지 않는다.** 작은 용량, 잘못된 길이, NULL, 부분 겹침, 키 준비의 할당·EVP 오류를 각각 검사한다. 여러 오류를 동시에 준 경우 특정 우선순위를 호환성 계약으로 삼지 않는다.
- 비NULL 포인터는 선언한 범위만큼 유효한 C 객체를 가리켜야 한다. opaque 컨텍스트는 정상 생성되어 아직 해제되지 않았어야 한다. 임의 주소·dangling pointer·초기화하지 않은 포인터를 라이브러리가 안전하게 판별할 수 있다고 약속하지 않는다.
- 다른 객체 포인터끼리 `<` 비교·뺄셈하지 않는다. 지원하는 평탄 주소 플랫폼의 `uintptr_t` 표현을 사용해 범위 끝 덧셈의 overflow를 먼저 검사한다. `UINTPTR_MAX`가 없는 환경은 빌드에서 지원하지 않음을 명시한다. 정수 범위 검사가 유효하지 않은 포인터를 안전하게 만드는 것은 아니다.
- 컨텍스트 내부 저장소와 입출력 버퍼를 의도적으로 겹치게 만들지 않는 것은 호출자 전제다. 입력/출력 인자로 주어진 두 범위의 부분 겹침은 위 계약대로 검사한다.

소거는 `OPENSSL_cleanse` 등 최적화 제거를 방지하는 수단을 사용한다. 레지스터·OS 복제·덤프까지 모든 사본이 지워진다는 보장은 하지 않는다. 비밀 의존 분기/주소를 피하는 C 코드와 실제 컴파일 결과에서 검토한 범위를 구별한다.

## 5. 고정 벡터와 기능 검증

### 5.1 SHAKE256 어댑터 KAT

빈 입력을 64바이트로 확장한 결과:

```text
46b9dd2b0ba88d13233b3feb743eeb243fcd52ea62b81b82b50c27646ed5762fd75
dc4ddd8c0f200cb05019d67b592f6fc821c49479ab48640292eacb3b7c4be
```

위 두 줄을 연결한 64바이트다. 생산에서는 `EVP_DigestFinalXOF`의 요청 바이트 수와 성공 값을 확인한다. 같은 문맥에 final을 반복 호출해 임의 스트리밍 XOF처럼 사용하지 않는다.

### 5.2 Interlock KAT

모든 hex는 바이트 배열 표현이다. 아래 첫 라운드키 4개만 LE32로 해석된 정수 표기다.

| 항목 | 값 |
| --- | --- |
| key | `0000000000000000000000000000000000000000000000000000000000000000` |
| plaintext | `00000000000000000000000000000000` |
| 첫 라운드 k0,k1,k2,k3 | `634a205d`, `d56cc590`, `d6cf518c`, `9c8022bf` |
| 1라운드 출력 | `bc3f5fdced85606be7d9ad9f4bd37a1e` |
| 4라운드 출력 | `44045d030a10d4ccae45aa9b54964b1a` |
| 28라운드 출력 | `46272f4086f471ad8a7ec9c9917912bb` |

추가 전체 28라운드 벡터:

| key | plaintext | ciphertext |
| --- | --- | --- |
| `000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f` | `000102030405060708090a0b0c0d0e0f` | `55b8e32c0f8b46ab083cb4a21150c3e8` |
| `ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff` | `ffffffffffffffffffffffffffffffff` | `f8c5d0db5d69b06a2ef4398b6b4f55d6` |
| `0000000000000000000000000000000000000000000000000000000000000000` | `01000000000000000000000000000000` | `52e7cbd4aa223cdbf3232c0f9c1b75e0` |

이 값들은 사양용 기대값이다. 새로운 Work 구현이 이미 통과했다는 뜻이 아니며 외부 인증 벡터도 아니다. 암호화뿐 아니라 각 암호문에서 평문 복구와 in-place 양방향을 검사한다.

### 5.3 독립 대조·오류 테스트

- 고정 KAT는 실행 중 다시 생성해 기대값으로 덮어쓰지 않는다. Python oracle과 C의 전체 키 일정, 0..28라운드 상태와 역변환을 **1,024개 key/block**에서 비교한다. 0..28라운드 대조는 `BUILD_TESTING=ON`의 비공개 검증 target에서 가능하며 연구 옵션을 요구하지 않는다.
- test seed는 `20261109`. 사례 `j`의 바이트는 `SHAKE256(ASCII("Interlock-128/test") || 0x00 || LE32(20261109) || LE32(j),48)`의 앞32B를 키, 뒤16B를 블록으로 쓴다. 이는 테스트 데이터 생성 규칙이지 제품 난수 생성 API가 아니다.
- `check-differential` target은 위 **독립 구현 결과 대조**를 뜻한다. 차분 공격 실험은 `research-*`에서 따로 실행한다.
- C 드라이버는 한 줄의 공백 구분 `operation rounds key_hex block_hex`을 받고 결과 hex 한 줄을 낸다. JSON 파싱은 Python이 담당한다. 일반 API 드라이버와 테스트용 prefix 드라이버는 빌드 target을 분리하며 prefix 드라이버는 제품에 설치하지 않는다.
- `input_len`은 0/1/15/16/17 및 큰 정수, 용량은 0/15/16/17을 다룬다. 실제 메모리는 유효하게 확보하고, 비정상 길이를 거부하기 전에 읽거나 쓰지 않는지 검사한다.
- `input/output`의 같은 버퍼, 분리 버퍼, ±1..15바이트 부분 겹침, 경계 sentinel을 검사한다. 할당·EVP 실패는 테스트 전용 주입 지점으로 재현하며 제품 API로 노출하지 않는다.
- ASan/UBSan은 유효 객체 범위 내에서 만든 입력·인자 조합을 검사한다. 미초기화 포인터 자체를 넘기는 UB 테스트를 정상 오류처리 검증으로 사용하지 않는다.

## 6. 이번 범위에 포함할 연구

과거 감사에서 보고된 축소 라운드 성질을 새 코어에서 재현한다. 다음은 **현재 실행 결과가 아니라 재현할 기대 성질과 실험 조건**이다.

### 6.1 정확 계산과 1라운드 서브키 복구

S-box DDT는 입력16개를 전수 계산한다. 입력차분 비영 행의 최대 빈도는 `4/16`. Walsh LAT의 입력·출력 비영 마스크 최대 절댓값은 `8`이고 정규화 상관 절댓값은 `8/16`. 하위 비트부터 좌표 차수는 `2,3,3,3`이다. `L32` 행렬의 열을 `L32(1<<j)`로 구성해 GF(2) 소거로 rank32와 역행렬을 구한다.

1라운드 평문 `(a,b,c,d)`와 출력 `(o0,o1,o2,o3)` 한 쌍으로:

```text
A = ROR32(o1,13)
D = ROR32(o2,21)
k0 = b ^ S_inverse(L32_inverse(A ^ a))
k3 = A ^ S_inverse(L32_inverse(D ^ d))
```

복원값을 진짜 첫 라운드키와 대조하고 다른 평문/암호문에서도 같은 FS 관계가 성립하는지 확인한다. full 실험은 1,024키 × 서로 다른 평문 2개, smoke는 8키다. 복원되는 것은 **첫 라운드 확장키 중64비트**이며 256비트 마스터키나 28라운드 키 복구가 아니다.

### 6.2 2라운드·3라운드 구별자

동일 키에서 평문 차분을 LE32 `(1,0,0,0)`으로 고정한다.

- **2라운드:** 출력 첫 워드 차분은 `{0x04004801,0x6c001800,0x94006801,0xfc003800}` 중 하나다.
- **3라운드:** 출력 두 번째 워드 차분에 `0x001f001f`를 AND한 값이 0이다. 워드 번호는 0부터, 워드 내부 비트도 LSB=0부터 센다.
- full은 128키 ×128쌍, smoke는 8키 ×32쌍이다. 확정 성질의 반례는 원인 분석 대상이며 통계 오차로 덮지 않는다.

2라운드 집합의 계산: `D={S(x)^S(x^1) : x=0..15}={3,7,9,13}`. 각 `s∈D`에 `ROL32(L32(s),26)`를 적용하면 위 네 값이 나온다.

3라운드 지지집합의 계산: `N(m)`은 m에서 하나라도 켜진 비트를 가진 각 니블 전체를 `0xf`로 확장한 마스크, `U(m)=N(m)|ROL32(N(m),3)|ROL32(N(m),17)`이다.

```text
W0 = ROL32(U(1),26)                  = 0xfc007801
W1 = ROL32(U(1<<13),13)              = 0xfe003c00
support = ROL32(W0 | U(W1),13)        = 0xffe0ffe0
forced_zero = (~support) & 0xffffffff = 0x001f001f
```

이는 가능한 차분 비트의 상계다. XOR 상쇄는 지지집합을 늘리지 않는다. 이상적인128비트 랜덤 순열에서 두 서로 다른 출력이 우연히 위 조건을 만족할 확률은 각각 `4*2^96/(2^128-1)`과 `(2^118-1)/(2^128-1)`이다. 이 축소 라운드 결과에서 전라운드 공격이나 `28-3`라운드의 보안 여유를 산출하지 않는다.

### 6.3 유한 차분 스크리닝

- 출력 비트 b는 직렬화 바이트 `b//8`의 비트 `b%8`이다. 범위0..127. 입력차분도 같은 번호 체계를 쓴다.
- discovery full: 라운드 `{4,8,16,28}` 각각에서 입력 단일비트128개 ×1,024평문쌍, 출력128비트의 반전 횟수를 센다. 라운드마다 `abs(2*count-N)`가 가장 큰 후보 하나를 선택하고 동률이면 입력비트, 출력비트가 작은 것을 택한다.
- holdout full: 선택한 네 후보를 discovery와 다른 키4개 및 새 표본에서 각각32,768쌍으로 확인한다. discovery 결과와 holdout 결과를 분리한다. smoke는 라운드 `{4,28}`, 입력비트 `{0,31,63,95,127}`, 각128쌍과 holdout 1키×256쌍이다.
- 연구 seed는 `20261109`. 입력 생성은 `SHAKE256(ASCII("Interlock-128/research")||0x00||ASCII(label)||0x00||LE32(seed)||LE32(rounds)||LE32(input_bit)||LE32(key_index),out_len)`. label은 `key`, `discovery`, `holdout`으로 분리한다. 키는 round/input fields를0으로 고정한 `key` label32B; discovery 키 index0, holdout index1..4를 사용한다. 평문은 각 실험 스트림을16B씩 나눈다.
- 반전횟수·표본수·비율과 Wilson95% 구간을 기술통계로 기록한다. 별도로 가족 단위 비교를 하면 검사 수와 보정을 명시한다. 선택 후의 discovery p-value를 새 증거처럼 쓰지 않는다. 난수처럼 생성된 고정 표본의 미검출을 안전성 증명으로 해석하지 않는다.
- 이 검사는 단일 입력차분·출력비트 수준이다. 전체 trail/hull 탐색, MITM·boomerang·관련키·대수 공격을 전부 구현할 의무는 없다. 이들은 범위와 필요한 자원을 적은 후속 연구 항목이다.

`research-full`은 정해진 사례 수를 끝내면 종료한다. 기본 시간 예산은20분이며 초과 시 이미 완료한 사례와 `incomplete` 상태를 저장한다. 자동으로 예산을 늘려 무한 실행하지 않는다. `research-smoke`는 기본 CI에서2분 제한으로 수행한다. 확률적 편향 수치를 CI 합격 조건으로 삼지 않고 실행 정합성과 정확한 invariant만 검사한다.

## 7. 성능 측정과 호환 최적화

제품 전체28라운드만 측정한다. 최소5개 반복 표본, warmup, 충분히 큰 반복 수와 최적화 제거 방지 checksum을 사용한다. 입력 생성·출력 인쇄는 측정에서 제외하고 실제 시간 경계를 결과에 적는다.

| 측정 항목 | 포함/제외 |
| --- | --- |
| 준비된 키의 암호화·복호화 | 공개 API의 검사와16B 블록 처리 포함. 키 생성 제외 |
| 내부 코어 처리 | 필요 시 연구 target에서 별도 측정. 공개 API 수치와 혼합 금지 |
| 키 준비 | 할당·SHAKE·448B 일정 생성 포함. 생성과 해제 비용 구간을 각각 기록 |
| 새 키와1블록 | `interlock_key_ctx_create`+암호화+소거·해제의 전체 사용 비용 |
| 연속 처리 | 준비된 키로16B/1KiB/16KiB/1MiB 입력에 독립 블록 API를 반복한 비용. 운용모드 제공이라는 뜻이 아님 |

OpenSSL AES-256의 패딩 없는 블록 처리도 참고 측정한다. 이는 벤치마크용이며 ECB 파일 암호화를 권하는 것이 아니다. 하드웨어 가속 여부, 준비/호출 비용, 단일 블록과 배치의 차이를 표시한다. 동일 보안 수준이 증명된 비교라고 쓰지 않는다.

호환 최적화는 같은 KAT·전체 prefix 대조·연구 invariant를 통과해야 한다. 실험용 코드 변형은 작업 중 임시 디렉터리나 Git 차이로 관리하고 완성 저장소에 여러 후보 코어를 병렬 보관하지 않는다. 개선이 재현되지 않으면 현재 코어를 유지하고 측정 결과를 남긴다. 이 경우도 최적화 평가 작업은 결과가 있는 것이며 빈 기능 커밋을 만들 필요가 없다.

과거 감사 참고 수치인 준비된 코어 약14.97MiB/s는 특정 공유 x86_64 호스트의 값이다. 새 opaque API·검사·환경 수치로 자동 승계하지 않는다. **현재 구현의 실측표와 과거 참고표를 분리**하고, 정하지 않은 경쟁군의 평균 이상 또는 검증되지 않은 보안 강도를 주장하지 않는다.

## 8. 확정 커밋로그

커밋 수는 **32개**이며 번호는 계획 번호다. 각 검증은 앞 단계의 테스트까지 유지한 상태에서 실행한다. 아직 없는 target을 먼저 실행했다고 기록하지 않는다.

### Phase 1 기반과 빌드 — 1~5

| 번호 | 실제 커밋 제목 | 구현·산출물 | 완료 검증 |
| ---: | --- | --- | --- |
| 1 | `docs: define clean-room implementation scope` | 신규 대상·범위, `docs/spec_ko.md`, 계획과 진행표, README | 옛 원격 의존/기존 코드 승계 지시가 없고 32개 계획이 일치 |
| 2 | `feat: configure portable c11 build` | CMake/CTest, 의존성 탐지, 생성물 제외, 실제 정수폭 검사 | fresh configure/build 및 `CHAR_BIT==8`·고정폭 정수 테스트 |
| 3 | `feat: add defined word and buffer operations` | LE load/store, 회전, 주소범위 overflow·overlap 검사 | 0/1/31/32회전, 비정렬 입력, 경계·중첩 표 테스트 |
| 4 | `feat: add verified shake256 adapter` | EVP XOF 어댑터, 실패 경로, 임시 비밀 소거 | 빈 입력64B KAT, 분할 update, 448B 요청 및 실패 주입 |
| 5 | `test: establish cross-platform build checks` | Linux GCC/Clang·Windows MSVC·macOS CI | 현재 존재하는2~4번 테스트 실행, 지원 환경별 성공/차단 구분 |

### Phase 2 전체 암호 코어 — 6~13

| 번호 | 실제 커밋 제목 | 구현·산출물 | 완료 검증 |
| ---: | --- | --- | --- |
| 6 | `feat: implement constant-time nibble substitution` | 비밀 인덱싱 없는 C S-box | 니블16입력×8위치 전수, 인접 니블 오염 없음 |
| 7 | `feat: implement linear and nonlinear mixing` | L32/FS/FM | 정의식 별도 계산과0/최댓값/단일비트·carry 경계 대조 |
| 8 | `feat: implement ordered forward rounds` | 갱신 순서·마지막 재배열 | 제공한 첫4서브키와0블록의1R KAT, 순차 갱신 중간값 |
| 9 | `feat: implement reverse round transitions` | 역회전·역갱신 | 4,096상태·서브키 묶음의1R 정역 왕복 |
| 10 | `feat: expand complete round key schedules` | 448B 전체 일정 및 prefix 규칙 | 첫4서브키·길이·NUL 정확성, 1R/4R/28R 기대값 |
| 11 | `feat: add immutable key contexts` | opaque 생성·소유권·해제 API | 원본 키 변경이 ctx를 바꾸지 않음, 실패시 슬롯 보존, `free(NULL)` |
| 12 | `feat: expose full-round block encryption` | 전체28R 암호화 공개 API | 네 전체 KAT, exact in-place, 길이·용량·중첩 오류와 출력불변 |
| 13 | `feat: expose full-round block decryption` | 전체28R 복호화 공개 API | 네 KAT 역변환·양방향 in-place·후방 sentinel 보존 |

### Phase 3 독립 검증과 구현 안전성 — 14~19

| 번호 | 실제 커밋 제목 | 구현·산출물 | 완료 검증 |
| ---: | --- | --- | --- |
| 14 | `test: add independent reference oracle` | 명세에서 새로 쓴 Python oracle와 고정 JSON 벡터 | 제공된 KAT 일치, C 코어 호출/복사 없는 기준 계산 |
| 15 | `test: compare all round prefixes` | C 검증 드라이버와 `check-differential` | 1,024사례×0..28 prefix, 전체 일정, 역변환 일치 |
| 16 | `test: cover buffer and lifetime contracts` | API 부정·실패 주입·동시 읽기 테스트 | 5.3의 경계/중첩/실패출력 보존, 정상수명만 사용 |
| 17 | `test: add sanitizer and deterministic fuzz checks` | ASan/UBSan 옵션, 고정 seed 인자 조합 | Linux GCC/Clang sanitizer 검사, 보고된 오류0·미실행 별도 표기 |
| 18 | `test: verify external c consumer builds` | 공개 헤더+라이브러리만 링크하는 소비자 | 내부 헤더 없이 생성→암호화→복호화→해제, 제품에 연구 entrypoint 없음 |
| 19 | `test: audit secret-dependent code paths` | 비밀 흐름 점검과 대표 컴파일 산출물 검토 기록 | S-box·분기·주소·소거 검토 범위/미검사 항목을 구체 기록 |

### Phase 4 범위를 정한 암호분석 — 20~26

| 번호 | 실제 커밋 제목 | 구현·산출물 | 완료 검증 |
| ---: | --- | --- | --- |
| 20 | `feat: add reproducible research harness` | seed·사례·코드해시·결과JSON, 연구 target | 같은 seed에서 같은 입력, 실패/timeout 구분, 제품코어 분리 |
| 21 | `test: reproduce outer subkey recovery` | 연구 전용 S 역치환·GF(2) 소거 기반 L32 역행렬 helper와 1R k0/k3 복구·다른 평문 확인 | 32기저에서 L32 역행렬 항등, smoke8키/full1,024키 복구값과 확장키 정확 일치 |
| 22 | `test: reproduce reduced-round differential constraints` | 2R 네값 집합, 3R mask 및 지지집합 계산 | full128키×128쌍과 정확 계산; 반례면 원인 분석 |
| 23 | `feat: calculate exact component properties` | DDT/LAT/차수/선형rank 계산과 21번의 역행렬 helper를 사용한 결과 보고 | 작은 입력 전수,6.1기대값·역행렬 항등 일치 |
| 24 | `feat: screen registered differential masks` | 정해진4/8/16/28R discovery sweep | 입력128×표본1,024, 후보 선택과 동률 규칙 재현 |
| 25 | `test: validate findings on independent holdouts` | 독립4키×32,768표본 후속 검증 | discovery와 분리된 데이터,4후보 결과/구간·미검출 한계 저장 |
| 26 | `docs: record attack scope and unresolved questions` | 보안 문서, 성공공격·계산예산·미탐색 정리 | reduced/full 범위·키복구 대상 명확, 실행한 full결과 또는 incomplete 표시 |

### Phase 5 성능과 호환성 평가 — 27~30

| 번호 | 실제 커밋 제목 | 구현·산출물 | 완료 검증 |
| ---: | --- | --- | --- |
| 27 | `feat: measure setup and block processing costs` | native bench와7절의 비용 구분 | 최소5표본·checksum·정확성 확인·환경·측정 경계 기록 |
| 28 | `feat: add aes reference measurements` | OpenSSL AES-256 참고 벤치 | 같은 호스트/길이·padding off·가속/초기화/호출조건 표기 |
| 29 | `test: evaluate bit-compatible scalar optimizations` | 최소1개 실제 호환 최적화 실험과 전후 결과; 유효한 개선만 반영 | KAT·prefix·공격회귀 재통과, 효과 없으면 코어 유지와 평가 결과 기록 |
| 30 | `docs: report reproducible performance results` | 현재 성능표·재실행 명령·과거참고 분리 | 준비/블록/전체비용 누락 없음, 하드웨어가 다른 수치의 직접 우열 금지 |

### Phase 6 인계 — 31~32

| 번호 | 실제 커밋 제목 | 구현·산출물 | 완료 검증 |
| ---: | --- | --- | --- |
| 31 | `docs: finalize implementation and research handoff` | README/API/보안/성능/진행 문서와 검토 요청 목록 | 첫 사용자에게 숨은 ZIP·옛대화 필요 없음, 라이선스 미정이면 명시 |
| 32 | `test: verify clean-checkout acceptance` | 새 레포 clean checkout 재현 검사와 검증 기록 | 9절 전항목 실제 상태, 원격SHA·CI확인 또는 정확한 차단 사유 보고 |

## 9. 빌드 명령과 인수 기준

### 9.1 재현 명령

아래 명령은 해당 target이 추가된 이후에 사용한다. `BUILD_TESTING`은 ON, 연구·벤치 옵션 기본값은 OFF로 정의하고 여기서는 전체 재현을 위해 켠다.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCRYPTO_BUILD_RESEARCH=ON -DCRYPTO_BUILD_BENCHMARKS=ON
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
cmake --build build --config Release --target check-differential
cmake --build build --config Release --target research-smoke
cmake --build build --config Release --target research-full
cmake --build build --config Release --target bench
```

OpenSSL 탐지는 CMake `find_package(OpenSSL 3.0 REQUIRED COMPONENTS Crypto)`와 `OpenSSL::Crypto`를 사용한다. Python은 테스트/연구를 켰을 때 탐지한다. Windows에서는 필요하면 실제 설치된 `OPENSSL_ROOT_DIR`를 지정하고 Multi-config 빌드의 `--config`를 유지한다. 설치 경로나 이미 설치됐다는 사실을 추측하지 않는다.

Linux GCC/Clang sanitizer 별도 빌드:

```sh
cmake -S . -B build-sanitize -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON -DCRYPTO_ENABLE_SANITIZERS=ON
cmake --build build-sanitize
ctest --test-dir build-sanitize --output-on-failure
```

`CRYPTO_ENABLE_SANITIZERS` 기본 OFF. 지원 compiler에서만 ASan+UBSan을 설정하고 MSVC에 GCC 플래그를 전달하지 않는다. LeakSanitizer 등을 환경상 실행하지 못하면 검사 범위에서 제외했다는 사실을 남기며 전체 통과로 바꾸지 않는다. 정기 CI는 빠른 기능 검사·작은 연구 smoke 위주이며 전체 통계 실험·성능 수치의 우열은 CI 통과 조건으로 쓰지 않는다.

### 9.2 최종 인수표

- 네 KAT와 전체 prefix 대조, API·실패 경로·정역변환 검사가 실행됐다.
- 세 OS 계열 빌드의 실제 결과와 Linux GCC/Clang ASan·UBSan 결과가 구분되어 있다. 환경이 없는 항목은 미검증이다.
- 1R 서브키 복구,2R/3R 구별자, 정확 부품 계산, 등록된 discovery/holdout가 실행되거나 예산 초과 상태로 기록됐다. 정확 성질 미재현은 해결 전 성공 처리하지 않는다.
- 키 준비/준비된 블록/새 키 전체 비용과 AES 참고값을 같은 측정 조건 설명과 함께 제공한다.
- 새 원격의 실제 마지막 SHA와 CI 상태가 있다. 원격이 차단됐다면 로컬 SHA와 필요한 조치가 있다.
- 제품 라이브러리에 축소 라운드·내부 상태 출력이 없고, 결과를 실제 기밀 보호 안전성으로 과장하지 않는다.

최종 보고는 완료한 계획 범위·추가 수정 커밋·테스트·원격 상태·남은 항목 순서로 짧게 작성한다. 무제한 암호분석이나 성능 목표 달성을 이유로 전체 작업을 끝없이 연장하지 않는다. 실질적인 전라운드 결함이 발견되면 공개 설명과 사용 가능성 판정을 즉시 수정하고 재설계는 별도 승인받는다.

## 10. 외부 규격 참고

- [NIST FIPS 202 — SHAKE256 정의](https://csrc.nist.gov/pubs/fips/202/final)
- [OpenSSL 3 EVP digest/XOF API](https://docs.openssl.org/3.0/man3/EVP_DigestInit/)

이 링크들은 표준 의존성 확인용이며 Interlock 자체의 보안성 증명이 아니다. Interlock의 고유 수식·도메인·KAT·실행 계획은 이 문서에 포함되어 있으며 외부 자료를 읽어 빈 설계를 추측하도록 하지 않는다.
