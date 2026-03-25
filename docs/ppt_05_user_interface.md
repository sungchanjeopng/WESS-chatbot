# ENV200 사용자 인터페이스 가이드

## 컨트롤러 전면부
- User Input: 버튼 (UP, DOWN, ENTER, ESC 등)
- User Output: LCD 디스플레이

## 주요 화면

### 화면 전환
UP/DOWN 버튼으로 화면 간 순환 가능:
숫자형 화면 → 정보 화면 → 그래프 화면 → (순환)

### 숫자형 화면 (Numeric)
| 위치 | 표시 내용 |
|------|-----------|
| 상단 | 날짜, 시간, 언어 |
| 중앙 | 현재 농도값 (대형 숫자) |
| 하단 좌 | 온도 (°C) |
| 하단 우 | 전류 출력 (mA) |
| 우측 | 단위 (%) |

### 정보 화면 (Information)
| 항목 | 표시 내용 |
|------|-----------|
| EEA (Damp) | 댐핑 적용된 EEA 값 |
| Frequency | 현재 주파수 |
| Damping | 댐핑 설정값 |
| Max. Range | 최대 측정 범위 |
| Pipe OD | 배관 외경 설정 |
| AGC | 자동 게인 상태 |

### 그래프 화면 (Graph)
- 측정값의 시간별 추이를 그래프로 표시

## 메뉴 구조

### 메뉴 접근
1. ENTER 버튼 길게 누르기
2. Passcode 입력 (기본값: 0000)
3. 메뉴 진입

### 메인 메뉴
```
MENU
├── Measurement (측정)
│   ├── Density Unit (농도 단위: %)
│   ├── Pipe Diameter (배관 외경: 0H~2H)
│   ├── Detection Area (검출 범위)
│   ├── Frequency (주파수)
│   ├── Calibration (교정)
│   ├── Damping (댐핑: 60)
│   └── Offset (오프셋: 0.00)
├── Output (출력)
│   ├── SET 4mA
│   ├── SET 20mA
│   ├── Trim 12mA
│   ├── Trim 20mA
│   ├── Output 4mA (수동 출력)
│   ├── Error Delay
│   └── Error Output
├── Data (데이터)
│   ├── Saving Interval (저장 간격: 1M)
│   ├── Download (다운로드)
│   ├── Delete (삭제)
│   └── Saved Count (저장 건수)
└── System (시스템)
    ├── Passcode (비밀번호)
    ├── Language (언어)
    ├── Time (시간)
    └── Version (펌웨어 버전)
```

### 파라미터 설정
- UP/DOWN 버튼으로 항목 이동
- ENTER 버튼으로 선택/확인
- ESC 버튼으로 이전 화면/취소
- 숫자 입력 시 UP/DOWN으로 값 변경 후 ENTER로 저장
