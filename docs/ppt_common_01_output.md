# 공통 출력 섹션 가이드

## 1. 전류 출력 (Current)

### 4mA / 20mA 설정
- Set 4mA: 4mA에 해당하는 계면 레벨값 (m)
- Set 20mA: 20mA에 해당하는 계면 레벨값 (m)
- 측정값이 Set 4mA ~ Set 20mA 범위에서 4~20mA로 비례 출력

### Trim (미세 조정)
- Trim 12mA: 중간점 미세 조정 (기준 50, 범위 0~99)
- Trim 20mA: 상한점 미세 조정 (기준 50, 범위 0~99)
- 50이 기준(보정 없음), 50보다 크면 출력 증가, 작으면 감소

### Output 4mA
- 수동으로 4mA를 출력하여 루프 테스트 가능

### Error Delay / Error Output
- Error Delay: 에러 판정 대기 시간 (20~990초, 기본 120초, 10초 단위)
- Error Output: 에러 발생 시 전류 출력 동작
  - 3.8mA: 하한 경보 전류
  - Hold: 에러 직전 출력값 유지
  - 21mA: 상한 경보 전류

## 2. 릴레이 (Relay)

### 릴레이 2채널 (R1, R2)

### R1 (상한 알람)
- ACT: 레벨이 동작값 이상이면 릴레이 ON
- STOP: 레벨이 정지값 이하이면 릴레이 OFF
- 예: ACT=4.00m, STOP=3.00m → 4m 이상이면 ON, 3m 이하이면 OFF

### R2 (하한 알람)
- ACT: 레벨이 동작값 이하이면 릴레이 ON
- STOP: 레벨이 정지값 이상이면 릴레이 OFF

### Relay Test
- 수동으로 릴레이 ON/OFF 테스트 가능

## 3. 통신 프로토콜 (Protocol)

### Standard
- 일반 시리얼 통신 (RS-232/RS-485)

### RF
- RF 무선 통신
- RF 채널: 1~4

### Modbus
- Modbus RTU 프로토콜
- 보레이트: 4800 / 9600 / 19200 bps
- 슬레이브 주소: 1~247
