# 공개 API 계약

공개 헤더는 `include/interlock.h` 하나입니다. OpenSSL 타입과 컨텍스트의 내부 필드는 노출하지 않습니다. 키는 32바이트, 블록은 16바이트입니다.

`interlock_key_ctx *ctx = NULL;`로 초기화한 뒤 `interlock_key_ctx_create(&ctx, key, 32)`를 호출합니다. 성공한 컨텍스트는 확장키 112워드를 소유합니다. 원본 키를 수정하거나 소거해도 준비된 일정은 변하지 않습니다. 호출자는 자신의 원본 키를 소거할 책임이 있습니다.

생성 실패는 `ctx` 슬롯을 변경하지 않습니다. 기존 비NULL 슬롯을 덮어쓰지 않습니다. 슬롯과 키 입력의 범위가 겹치면 거부합니다. 비NULL 포인터는 선언한 길이의 유효 객체를 가리켜야 합니다.

컨텍스트는 생성 후 불변이며 전역 가변 scratch가 없습니다. 읽기 전용 재사용 시 서로 겹치지 않는 입출력을 사용하고, 실행 중 해제와의 동기화는 호출자가 담당합니다. 16번에서는 제품 라이브러리의 같은 컨텍스트를 4개 스레드가 공유하고 각자 분리된 입출력에서 4,096회 암호화·복호화하는 검사를 추가했습니다. 해제는 모든 join 후 수행합니다. 이 실험은 모든 스레드 스케줄의 증명이나 ThreadSanitizer 결과가 아닙니다.

`interlock_key_ctx_free(NULL)`은 아무 작업도 하지 않습니다. 정상 컨텍스트는 소유한 일정을 `OPENSSL_cleanse`로 소거한 후 해제합니다. 호출자는 해제 뒤 포인터를 NULL로 바꾸어야 합니다. 해제 후 사용, 이중 해제, 초기화하지 않은 포인터는 지원하지 않습니다. 소거는 레지스터·컴파일러가 만든 spill/ABI 스택 사본·운영체제 사본·덤프까지 없앤다는 보장이 아닙니다.

`interlock_encrypt_block(ctx, input, 16, output, output_capacity)`는 전체 28라운드만 처리합니다. 세 포인터는 비NULL이어야 합니다. 입력 길이는 정확히 16, 출력 용량은 16 이상이어야 합니다. 성공 시 처음 16바이트만 쓰고 뒤쪽 용량을 보존합니다.

정확히 같은 시작 주소인 in-place를 지원합니다. 서로 다른 시작 주소에서 16바이트 범위가 일부 겹치면 `INTERLOCK_EOVERLAP`입니다. 유효한 객체의 평탄 주소를 `uintptr_t`로 표현해 끝 주소 overflow를 검사하며 다른 객체 포인터의 비교·뺄셈은 사용하지 않습니다. 검증을 끝낸 후 로컬 상태에서 계산하고 마지막에 출력합니다. 오류 반환 시 출력은 전혀 변경하지 않습니다. 컨텍스트 내부 저장소와 입출력을 의도적으로 겹치지 않는 것은 호출자의 전제입니다.

상태 값은 성공 `INTERLOCK_OK`, NULL·기존 슬롯 등의 잘못된 인자 `INTERLOCK_EINVAL`, 길이 `INTERLOCK_ELENGTH`, 작은 용량 `INTERLOCK_ECAPACITY`, 겹침 `INTERLOCK_EOVERLAP`, 할당 실패 `INTERLOCK_ENOMEM`, OpenSSL 연산 실패 `INTERLOCK_ECRYPTO`입니다. 여러 오류가 함께 있을 때 우선순위는 계약하지 않습니다.

`interlock_decrypt_block`은 같은 인자·길이·용량·겹침·출력 보존 계약으로 전체 28라운드를 역순 처리합니다. 추가 swap, whitening, 패딩, 운용모드는 없습니다. 공개 API에는 라운드 수나 중간 상태를 요청하는 인자가 없습니다.

19번까지 독립 Python oracle, 전체 prefix 대조, 계약·동시성·sanitizer, 외부 C 소비자와 코드 경로 검토를 추가했습니다. 실행 결과와 한계는 validation_ko.md, sanitizers_ko.md, implementation_audit_ko.md를 참고합니다. 암호분석·성능과 최종 인수는 20번 이후 계획입니다.
