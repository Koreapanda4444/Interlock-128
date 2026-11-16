# 구현 안전성 검사

```sh
cmake -S . -B build-sanitize -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON -DCRYPTO_ENABLE_SANITIZERS=ON
cmake --build build-sanitize --config Debug
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 ctest --test-dir build-sanitize --output-on-failure
```

지원 GCC/Clang 드라이버에서 컴파일·링크에 `-fsanitize=address,undefined`를 적용하고 첫 진단에서 실패하도록 구성합니다. MSVC에는 GCC 플래그를 넘기지 않으며 해당 옵션을 켜면 지원하지 않는 조합을 명확히 거부합니다. Linux GCC/Clang CI에서 Release 검사와 별도 Debug ASan·UBSan·누수 검사를 실행합니다. 이 문서는 아직 실행하지 않은 플랫폼이나 컴파일러를 통과로 간주하지 않습니다.

`deterministic_fuzz`는 seed 20261109, 16,384개 고정 사례에서 정상 컨텍스트 또는 NULL, 유효한 실제 버퍼 내 오프셋, 입력 길이·출력 용량·겹침 조합을 검사합니다. 복수 오류의 구체적 우선순위는 고정하지 않습니다. 성공할 때는 분리 버퍼 호출 결과와 전체 메모리 변화를 대조하고, 실패할 때는 원본 전체 버퍼가 보존되어야 합니다. 해제 후 사용이나 임의의 비정상 주소를 주입하지 않습니다. 잘못된 SIZE_MAX 길이는 실제 작은 객체를 읽기 전에 거부하는 경로입니다.

이는 제한된 실행에서의 구현 결함 검사이며 모든 UB·메모리 오류의 부재나 암호학적 안전성 증명이 아닙니다. ThreadSanitizer·메모리 초기화 추적·의존 라이브러리 내부 전체 계측은 이번 검사의 범위가 아닙니다. LeakSanitizer가 환경상 실행되지 못하면 누수 통과로 바꾸지 않고 해당 환경 결과를 분리합니다.

설정 참고: [Clang ASan](https://clang.llvm.org/docs/AddressSanitizer.html), [Clang LSan](https://clang.llvm.org/docs/LeakSanitizer.html), [GCC instrumentation](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html).

17번 로컬 결과: Linux x86_64 GCC 14.2, OpenSSL 3.5.7에서 Release 16/16 및 Debug ASan·UBSan 16/16 통과. Debug는 `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1`로 실행했으며 주소·UB 진단 0건입니다.

누수 검사는 로컬에서 차단됐습니다. 암호 코어를 호출하지 않는 `test_platform`부터 `detect_leaks=1`에서 `LeakSanitizer does not work under ptrace` 진단과 실패 종료가 발생했습니다. 이 결과를 누수 통과로 처리하지 않습니다. 로컬에 Clang은 없으며 GCC/Clang CI의 `detect_leaks=1` 결과는 원격 실행 후 진행표에 별도 기록합니다.

17번 원격 실행에서 Linux GCC·Clang의 ASan·UBSan·누수 검사를 모두 통과했습니다. [CI 단계별 결과](https://github.com/Koreapanda4444/Interlock-128/actions/runs/42733975841). 실행 시 ASAN_OPTIONS의 detect_leaks는 1이며 로컬 ptrace 환경의 제외 설정을 적용하지 않았습니다.

26번 로컬 재검증: 연구 옵션 포함 Release22/22, Debug ASan·UBSan22/22 통과. 현재 환경에서도 detect_leaks=1의 test_platform은 ptrace 제약으로 실패했고, 로컬 주소·UB 검사는 detect_leaks=0으로 실행했습니다. 최신 CI는 계속 detect_leaks=1을 유지합니다. LSan 제외 상태를 누수 통과로 기재하지 않습니다.

최종 clean-checkout 인수에서는 벤치 smoke까지 켠 GCC14 Debug ASan·UBSan23/23이 통과했습니다. LSan의 ptrace 차단을 같은 새빌드에서 다시 확인했고 detect_leaks=0만 로컬에 적용했습니다. [인수 기록](acceptance_ko.md)과 CI의 detect_leaks=1 결과를 구분합니다.
