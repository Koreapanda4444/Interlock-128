# Clean-checkout 최종 인수

계획32번의 [실행기](../tests/check_acceptance.py)는 지정한 실제 Git commit을 `git clone --no-hardlinks --no-checkout`으로 복제하고 detached checkout합니다. 이전 build·설치 prefix·연구 캐시는 가져오지 않습니다. 원격 SHA는 GitHub 도구로 별도 대조하며 실행기가 인증 없는 네트워크 clone에 성공했다고 주장하지 않습니다.

[인수 기준선 JSON](acceptance_baseline.json)은 원격31번 `9c93974a0edb8d155788a6613bea111daed75aa2`에서 실행한 모든 단계·반환값·로그 해시·소스 해시입니다. 32번 자신의 SHA와 최종 원격 CI는 인계 응답에 기록합니다. 자기 SHA를 문서에 삽입하려고 추가 커밋하지 않습니다. 32번은 실행기와 이 기록·문서를 추가하며 제품 코어·API·KAT를 변경하지 않습니다.

| 명세9절 기준 | 실제 결과 |
| --- | --- |
| 네 KAT·API·실패·정역·수명·동시성·1,024개 모든 prefix | 새 Release CTest23/23, 별도 check-differential target 성공 |
| 소스/제품 격리·설치·재배치·외부 C 소비자 | 전체 구성과 제품 단독 구성 모두 성공; 내부 헤더/축소 라운드 진입점 미설치·심볼 부재 |
| 연구 실행 | 별도 smoke/full target 성공, full6단계 complete; exact·복구·구별 조건·선택 후보·holdout cohort가 등록 기준선과 동일 |
| 성능/AES | bench target33항목·각5표본 완료; 별도 bench-only 구성 성공; 결과는 이 호스트의 성능 참고 |
| 독립 옵션 | BUILD_TESTING=OFF 제품 전용, 연구 전용, 벤치 전용 구성·실행 성공 |
| 메모리 계측 | GCC14 Debug ASan·UBSan23/23, 주소/UB 진단0; 로컬 LSan은 ptrace 차단이며 누수 통과 아님 |
| 원격 플랫폼 | 31번 Linux GCC/Clang(누수검사 ON)·macOS 성공 확인; 최종 Windows 및32번 전체 CI 상태는 인계에서 보고 |
| 코어 고정 | 공개 헤더와 제품5파일 SHA256이19번 검토 기준선과 동일 |
| 안전성 해석·라이선스 | 제한된 연구 기준선으로 유지; 미해결 분석·라이선스 결정은 handoff/security 문서에 명시 |

사용한 로컬 환경은 Linux x86_64, GCC14.2.0, OpenSSL3.5.7, Python3.12.14, CMake4.4.5입니다. 다른 플랫폼의 실제 결과는 해당 GitHub Actions 로그에 따릅니다. macOS 벤치의 짧은 warmup 처리는 추가 `fix:` 커밋으로 보완했고 수정 후 macOS CI를 확인했습니다. 계획32개 외 필요한 수정1개가 있습니다.

Linux의 새 경로에서 전체 검증을 반복하는 명령:

```sh
COMMIT=$(git rev-parse HEAD)
python3 tests/check_acceptance.py --source . --work build-acceptance/fresh-run --commit "$COMMIT" --cmake /actual/path/to/cmake --output build-acceptance/fresh-run.json
```

work는 저장소 아래 ignored build 디렉터리의 존재하지 않는 새 하위 경로여야 합니다. 실행은 실제 configure/build·명세9.1 target·제품 설치 소비자·옵션 독립 구성·sanitizer를 수행합니다. 실패하면 failed JSON과 단계별 로그를 남기며 성공으로 바꾸지 않습니다. 대량 원시 자료와 native binary는 커밋하지 않습니다.
