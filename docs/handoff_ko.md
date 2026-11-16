# 구현·연구 인계

## 현재 범위

규범 사양은 [spec_ko.md](spec_ko.md) 하나입니다. C11 전체28라운드 공개 API, OpenSSL SHAKE 키 확장, Python 독립 oracle, 모든 prefix·실패·버퍼·수명·동시성·sanitizer·설치 소비자 검사, 제한된 연구, 비용 측정과 AES 참고가 구현됐습니다. 계획1~31번을 마쳤고32번 clean-checkout 인수를 진행합니다. 공개 인터페이스의 키/블록 길이·도메인·KAT는 유지했습니다.

| 읽을 문서 | 확인할 내용 |
| --- | --- |
| [build_ko.md](build_ko.md) | 실제 의존성·옵션·처음부터 실행할 명령 |
| [api_ko.md](api_ko.md) | 유효 객체·NULL 초기화·부분 중첩 거부·출력 보존·수명·소거 |
| [validation_ko.md](validation_ko.md), [sanitizers_ko.md](sanitizers_ko.md) | 독립 대조와 실제 계측 범위·로컬 LSan 제외 |
| [implementation_audit_ko.md](implementation_audit_ko.md) | GCC 대표 산출물의 검토 범위와 spill 한계 |
| [research_ko.md](research_ko.md), [security_ko.md](security_ko.md) | seed/등록·성공한 축소 라운드 공격·holdout·미탐색 |
| [benchmark_ko.md](benchmark_ko.md) | 준비/해제/공개 블록/새 키 비용, AES 단일/배치·가속 조건, 미채택 최적화 |
| [progress_ko.md](progress_ko.md) | 계획32개와 실제 SHA·추가 수정·CI 이력 |

## 완료 판정의 구분

기능·메모리 계약 일치, 제한된 컴파일 산출물 검토, 축소 라운드 분석, 성능 측정을 구별합니다. 1R의 k0/k3 복구는 확장키64비트이며 마스터키나28R 복구가 아닙니다. 2R/3R 성질을 전라운드 보안 여유로 바꾸지 않습니다. discovery에서 고른 후보는 다른 키·새 표본의 holdout으로 확인했습니다. 4R/key4의 개별 Wilson 구간이0.5를 제외한 관측도 기록했고 다중 비교 확증으로 해석하지 않습니다.

스칼라 ANF 변형은 KAT·모든 prefix·full 연구 결과가 같았지만 속도가 일관되지 않아 기존 코어를 유지했습니다. AES 참고는 EVP 호출 단위·가속 사용 가능 조건이 다른 성능 참고이며 동일 보안 강도를 주장하지 않습니다. 제품은 연구 기준선이며 실제 기밀 보호의 승인이 아닙니다.

## 다음 검토에서 필요한 결정

- 공개 배포 전에 소유자가 저장소 라이선스를 선택해야 합니다. 현재 임의의 라이선스를 추가하지 않았습니다. OpenSSL 등 의존성의 고지는 각각의 라이선스에 따릅니다.
- 전체 trail/hull, 다중 차분·MITM·boomerang·관련키·대수 공격은 별도 범위·계산 예산을 정한 후 수행합니다. 현재 미검출은 안전성 증명이 아닙니다.
- 4R 관측의 원인을 확인하려면 새 seed/키군과 검사 수·예산·다중 비교 처리를 미리 정한 독립 실험이 필요합니다.
- compiler/CPU/provider별 실제 부채널·spill·더 넓은 기계어 검토와 전문 암호분석은 현재 검사와 분리합니다.

기존 ZIP·옛 채팅·다른 암호 프로젝트 없이 이 저장소에서 재현할 수 있습니다. GUI·운용모드·AEAD·언어 바인딩·배포 릴리즈는 이32개 계획에 포함하지 않습니다. 알고리즘 재설계는 별도 작업으로 다룹니다.
