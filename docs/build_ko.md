# 빌드와 검증 환경

CMake 3.20 이상, C11 컴파일러, OpenSSL 3.x 개발 파일이 필요합니다.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

13번 기준 검사는 platform, support, shake, substitution, mixing, forward, reverse, schedule, context, encrypt, decrypt의 11개입니다. `ctest --test-dir build -N`으로 현재 목록을 볼 수 있습니다. 후속 단계에서 실제 추가된 테스트가 같은 CTest 실행에 포함됩니다.

로컬 실행: Linux x86_64, GCC 13.3.0, CMake 4.4.4, OpenSSL 3.0.13. 위 11개 검사 통과. 현재 작업 환경에 Clang, Windows, macOS가 없어 로컬 실행 완료로 보고하지 않습니다. 원격 결과는 진행표에 해당 SHA와 함께 별도 기록합니다.

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
