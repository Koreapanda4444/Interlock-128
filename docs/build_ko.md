# 빌드와 검증 환경

CMake 3.20 이상, C11 컴파일러, OpenSSL 3.x 개발 파일이 필요합니다.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

19번 Linux x86_64 GCC/Clang 기준 검사는 기존 11개와 reference, differential, contracts, concurrency, deterministic_fuzz, external_consumer, code_path_inventory를 합한 18개입니다. macOS·Windows는 ELF x86 inventory를 제외한 17개입니다. `ctest --test-dir build -N`으로 현재 구성의 실제 목록을 볼 수 있습니다.

초기 1~13번 로컬 실행은 Linux x86_64 GCC 13.3.0·OpenSSL 3.0.13이었습니다. 14~19번은 새 빌드 디렉터리에서 GCC 14.2.0·OpenSSL 3.5.7·Python 3.12.14·CMake 4.4.4로 실행했습니다. 로컬 Clang·Windows·macOS 실행으로 표기하지 않으며 원격 CI 결과와 구분합니다. sanitizer의 로컬 LSan 제외 조건과 GCC/Clang CI의 실제 누수 검사 성공은 sanitizers_ko.md에 기록했습니다.

CI는 Linux GCC/Clang, macOS 기본 AppleClang, Windows MSVC x64를 구성합니다. Windows는 호스팅 러너의 `VCPKG_INSTALLATION_ROOT`에서 OpenSSL 개발 파일을 설치하고 실제 toolchain을 지정합니다. macOS는 Homebrew의 실제 prefix를 탐지합니다. 외부 의존성 설치·러너 가용성 장애와 코드 실패를 구분합니다.

러너 환경 참고: [공식 Windows 이미지 목록](https://github.com/actions/runner-images/blob/main/images/windows/Windows2025-Readme.md), [checkout v6 설명](https://github.com/actions/checkout/tree/v6). 러너 이미지의 변동에 따라 실제 실행 버전은 CI 로그에서 확인합니다.

공개 CMake 패키지 설치와 소비자 빌드:

```sh
cmake --install build --config Release --prefix /absolute/interlock-prefix
cmake -S tests/consumer -B build-consumer -DCMAKE_PREFIX_PATH=/absolute/interlock-prefix
cmake --build build-consumer --config Release
ctest --test-dir build-consumer -C Release --output-on-failure
```

위 prefix는 실제 설치 경로로 바꿉니다. Windows에서는 본체와 같은 OpenSSL/vcpkg toolchain·triplet을 소비자 configure에도 지정합니다. 자동 `external_consumer` 검사는 본체 configure 값을 전달합니다. OpenSSL은 별도 의존성이며 패키지가 자체 복제·배포하지 않습니다.
