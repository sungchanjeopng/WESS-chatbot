# ENV120 (C1S-210) 시스템 및 데이터 설정 가이드

## 시스템 메뉴
| 파라미터 | 설명 |
|----------|------|
| Passcode | 비밀번호 (0~9999, 기본: 0) |
| Language | 영어 / 한국어 / 중국어 / 일본어 |
| Time | 시간 설정 |
| Version | 펌웨어 버전 확인 (v7.2.3) |

## 데이터 메뉴
| 파라미터 | 설명 |
|----------|------|
| Save | 데이터 저장 ON/OFF |
| Download | 시리얼 다운로드 |
| Delete | 데이터 삭제 |
| Saving Interval | 저장 간격 (1분/10분/60분) |
| Display Term | 디스플레이 기간 |

## 메뉴 구조 (공개 섹션)
```
메인 메뉴
├── 1. 시스템 (System)
│   ├── Passcode
│   ├── Language (영/한/중/일)
│   ├── Time
│   └── Version
├── 2. 측정 (Measure)
│   ├── Page 1: Unit, Operation, Empty, Dead Zone, Echo AMP, Freq, TX Interval
│   ├── Page 2: Offset, Damping, Threshold, ASF, Window Reset, Window Range, 세정 간격
│   └── Page 3: 세정 시간, 측정 초기화, 공장 초기화
├── 3. 출력 (Output)
│   ├── Page 1: 4mA설정, 20mA설정, 12mA트림, 20mA트림, 4mA출력, 에러지연, 에러출력
│   └── Page 2: 릴레이1 Act/Stop, 릴레이2 Act/Stop, 릴레이테스트, 프로토콜
└── 4. 데이터 (Data)
    ├── Save ON/OFF
    ├── Download
    ├── Delete
    ├── Saving Interval
    └── Display Term
```
