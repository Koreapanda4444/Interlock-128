# 빌드와 전체 재현

CMake 3.20+, 8비트 바이트·uint32_t/uint64_t/uintptr_t를 지원하는 C11 compiler, OpenSSL 3.x libcrypto 개발 파일이 필요합니다. 테스트·연구·벤치 중 하나라도 켜면 Python 3.11+도 필요합니다. OpenSSL 내부 타입은 공개 헤더에 없습니다.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCRYPTO_BUILD_RESEARCH=ON -DCRYPTO_BUILD_BENCHMARKS=ON
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
cmake --build build --config Release --target check-differential
cmake --build build --config Release --target research-smoke
cmake --build build --config Release --target research-full
cmake --build build --config Release --target bench
```

Linux x86_64 GCC/Clang의 전체 구성은23개 CTest입니다. ELF inventory가 없는 Windows/macOS는22개입니다. `ctest --test-dir build -N`으로 실제 목록을 확인합니다. `research-full`은1,200초 고정 예산, smoke는120초입니다. 상태가 incomplete/failed면 완료로 취급하지 않습니다. 연구 원시 계수와 성능 결과는 build 아래에 생성합니다.

옵션 기본값은 `BUILD_TESTING=ON`, `CRYPTO_BUILD_RESEARCH=OFF`, `CRYPTO_BUILD_BENCHMARKS=OFF`, `CRYPTO_ENABLE_SANITIZERS=OFF`입니다. prefix 검증은 테스트 옵션만 켜도 가능하고 제품에는 포함되지 않습니다. 연구·벤치 옵션은 테스트를 끈 구성에서도 각각 독립적으로 빌드합니다.

제품만 빌드·설치하고 외부 C 소비자를 실행하는 예:

```sh
cmake -S . -B build-product -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DCRYPTO_BUILD_RESEARCH=OFF -DCRYPTO_BUILD_BENCHMARKS=OFF
cmake --build build-product --config Release
cmake --install build-product --config Release --prefix /absolute/interlock-prefix
cmake -S tests/consumer -B build-consumer -DCMAKE_PREFIX_PATH=/absolute/interlock-prefix
cmake --build build-consumer --config Release
ctest --test-dir build-consumer -C Release --output-on-failure
```

실제 prefix로 바꾸며 OpenSSL은 별도 의존성입니다. 테스트의 `external_consumer`는 설치→prefix 이동→공개 CMake 패키지만 사용하는 소비자 빌드와 nm/dumpbin 심볼 격리를 확인합니다. 내부 헤더·prefix/vector driver를 설치하지 않습니다.

Linux GCC/Clang ASan·UBSan:

```sh
cmake -S . -B build-sanitize -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON -DCRYPTO_BUILD_RESEARCH=ON -DCRYPTO_ENABLE_SANITIZERS=ON
cmake --build build-sanitize --config Debug
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 ctest --test-dir build-sanitize --output-on-failure
```

로컬 실행의 LSan은 ptrace에서 중단되어 `detect_leaks=0`의 ASan·UBSan 결과와 분리합니다. CI의 Linux GCC/Clang은 `detect_leaks=1`입니다. 상세 범위는 [sanitizers_ko.md](sanitizers_ko.md)에 있습니다. sanitizer 구성을 성능 비교에 사용하지 않습니다.

Windows MSVC x64에서는 실제 OpenSSL/vcpkg toolchain·triplet을 configure에 전달하고 `Release/`의 실행파일과 `--config Release`를 사용합니다. macOS는 Homebrew 등의 실제 prefix를 지정합니다. CI는 이를 탐지해 Ubuntu GCC/Clang·macOS AppleClang·Windows MSVC를 빌드합니다. 의존성 설치·runner 대기와 코드 실패를 구분하며 미실행 환경을 성공으로 간주하지 않습니다.

과거 로컬 결과:1~13번은 GCC13.3/OpenSSL3.0.13,14번 이후는 GCC14.2/OpenSSL3.5.7/Python3.12입니다. 현재 실측 환경은 결과 JSON과 해당 SHA의 CI 로그를 참조합니다.
