# 비밀 의존 경로 검토 기록 — 19번

검토한 소스와 대표 GCC 14.2 x86_64 Release 산출물에서 키·상태 값으로 분기 조건이나 데이터 주소를 선택하는 지점은 발견하지 않았습니다. 이 판단은 아래 모델과 산출물에 한정한 수동 검토 결과입니다. 모든 컴파일러·CPU에서의 constant-time 보장이나 타이밍 실험 결과가 아닙니다.

## 모델과 소스 흐름

비밀 데이터는 32바이트 키, 112개 확장키, 블록과 중간 상태입니다. 호출자의 유효한 객체 주소·길이·용량·정상 컨텍스트 수명, 고정 28라운드 번호는 공개 메타데이터로 취급합니다. 잘못된 포인터를 안전하게 판별한다는 모델은 아닙니다.

| 경로 | 확인한 데이터 흐름 | 판단 범위 |
| --- | --- | --- |
| S-box | 제품은 8개 니블을 Boolean ANF로 병렬 계산. 비밀값으로 표를 인덱싱하지 않음 | Python/C 테스트의 표 구현은 제품 외부 |
| L32·FS·FM | XOR, AND, unsigned 32비트 합, 정해진 상수 회전 | 상태·키 값으로 조건이나 회전 횟수를 선택하지 않음 |
| 정·역라운드 | 고정 28회, 일정의 고정 순번만 참조 | 키 내용은 로드한 값이며 주소 계산의 인덱스가 아님 |
| API 검사 | NULL, 길이, 용량, 주소 범위·겹침 검사 | 비밀 블록을 읽기 전에 검사. 복수 오류의 우선순위는 계약하지 않음 |
| 키 확장 | 고정 도메인 24바이트와 키 32바이트, XOF 출력 448바이트 | EVP 호출 순서와 크기는 키 값으로 바뀌지 않음. OpenSSL 내부는 미검토 |
| 생성·해제 | 할당 결과·EVP 성공 여부·슬롯 상태에 따른 오류 경로 | 데이터 값에 따른 분기가 아니라 호출 상태/자원 실패 경로 |
| 소거 | 명시적 stream, EVP 임시 출력, 컨텍스트, 블록 처리 임시 배열 | OPENSSL_cleanse 호출 보존 확인. 모든 기계어 사본 소거는 보장하지 않음 |

제품에는 가변 전역 scratch, 실패 주입 변수, 소거 관찰기, prefix 드라이버가 없습니다. `INTERLOCK_TESTING` 라이브러리의 관찰용 전역 변수는 별도 검사에만 쓰며 제품 동시성 검사는 그 라이브러리를 링크하지 않습니다.

## 대표 기계어 검토

Linux x86_64, GCC `14.2.0-19`, C11, `-O3 -DNDEBUG -Wall -Wextra -Wpedantic -Wconversion`, LTO·sanitizer 없이 생성한 archive의 세 제품 object와 10개 함수 구역을 검토했습니다. 실제 컴파일 명령·소스 해시·archive 해시·분기 목록 요약은 [audit_gcc14_x86_64.json](audit_gcc14_x86_64.json)에 있습니다. 다른 경로에서 빌드하면 매크로의 소스 경로 등으로 archive 해시는 달라질 수 있습니다.

| 함수 | 대표 산출물에서 확인한 내용 |
| --- | --- |
| `il_substitute` | 정적 명령 구역 78개 항목, 조건 분기 0, 명시적인 데이터 메모리 operand 0. 상수 shift/AND/XOR/OR 및 ABI push/pop. ret 뒤 alignment NOP는 데이터 접근으로 세지 않음 |
| `interlock_encrypt_block` | 조건 분기 8개 중 7개는 인자·겹침 검사, `0x29a`의 1개는 고정 키 일정 끝과 비교하는 라운드 반복. 키 로드는 순차 주소, 상태는 레지스터/고정 스택 offset |
| `interlock_decrypt_block` | 조건 분기 8개 중 7개는 같은 계약 검사, `0x5b0`의 1개는 역순 28회 반복. 키 주소 진행은 키 값과 무관 |
| `il_expand_key` | 포인터·길이·EVP 반환 분기와 고정 448바이트 복사 반복. 성공/EVP 실패 뒤 stream에 `il_cleanse` 호출 |
| `interlock_key_ctx_create/free` | 생성 실패와 정상 해제에서 448바이트 컨텍스트 소거 뒤 free. 기존 슬롯은 실패 시 보존 |
| `il_shake256`, 주소 helper, `il_cleanse` | 길이/주소/자원 상태 분기를 검토. 임시 XOF 출력은 OPENSSL_cleanse 뒤 CRYPTO_free, wrapper도 OPENSSL_cleanse 외부 relocation을 보존 |

위 offset과 항목 수는 이 GCC 산출물에만 해당합니다. 정적 항목 수는 실행 시간이나 성능 수치가 아닙니다. GCC의 키 일정 복사·직렬화에 자동 생성된 벡터 명령도 주소가 공개 반복/고정 offset에서 오는지 확인했습니다. 프로젝트에 SIMD 알고리즘을 새로 추가한 것은 아닙니다.

## 소거 한계와 미검토 항목

대표 S-box 산출물에는 callee-saved 레지스터의 push/pop이 있습니다. 명시적 배열과 컨텍스트의 소거를 확인해도 컴파일러가 만든 spill·ABI 스택 슬롯·레지스터의 모든 잔여 사본까지 지웠다고 할 수 없습니다. 모든 stack/register 사본 소거, 메모리 잠금, 코어 덤프 방지까지 제공한다는 주장은 하지 않습니다.

Clang·MSVC·AppleClang·다른 최적화 옵션/아키텍처의 기계어 전체, OpenSSL/provider/할당기 내부, CPU 미세구조·추측 실행·전력/전자기 누설, 타이밍 통계, ThreadSanitizer는 이번 수동 검토 범위가 아닙니다. 각 OS의 빌드·KAT·계약 테스트 성공과 그 플랫폼의 기계어 검토를 구분합니다. 축소/전체 라운드 암호분석과 보안 강도 판정은 20번 이후 범위입니다.

## 재현과 회귀 검사

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --config Release
cmake --build build --target check-code-paths
```

Linux x86_64 GCC/Clang에서 `code-path-inventory.json`과 `code-path-disassembly.txt`를 build 아래에 기록합니다. 명령·소스·산출물 해시와 조건 분기·메모리 operand·relocation 목록을 남깁니다. 자동 검사는 제품의 테스트 매크로/심볼 부재, 공개 심볼, 소거 relocation 보존을 확인합니다. 자동 taint 분석이나 비밀 의존성의 완전한 판별기가 아닙니다. Debug/sanitizer inventory도 별도 표시하며 위 Release 수동 검토와 같다고 취급하지 않습니다. macOS·Windows에는 이 ELF x86 inventory 검사를 등록하지 않으며, 공개 소비자와 심볼 격리 검사는 그대로 실행합니다.
