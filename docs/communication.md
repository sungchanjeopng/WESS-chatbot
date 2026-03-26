# ENV200 (C2S-211) 통신 설정 가이드

## Modbus RTU 통신

### 통신 사양
| 항목 | 사양 |
|------|------|
| 프로토콜 | Modbus RTU |
| 인터페이스 | RS-485 |
| 지원 보레이트 | 4800, 9600, 19200 bps |
| 기본 보레이트 | 9600 bps |
| 슬레이브 주소 범위 | 1 ~ 247 |
| 기본 슬레이브 주소 | 1 |
| CRC | CRC-16 (다항식 0xA001) |

### 지원 Function Code
| Function Code | 기능 |
|---------------|------|
| 0x03 | Read Holding Registers |
| 0x04 | Read Input Registers |
| 0x06 | Preset Single Register |

### Modbus 레지스터 맵

#### Input Registers (읽기 전용, Function Code 0x04)
| 주소 | 데이터 | 설명 |
|------|--------|------|
| 0x0000 | 농도값 (상위 워드) | 현재 측정 농도 |
| 0x0001 | 농도값 (하위 워드) | 단위에 따라 %, ppm, mg/L, g/L |
| 0x0009 | 온도값 | 현재 수온 (°C) |

### 통신 설정 방법
메뉴 > 출력 설정 > 프로토콜에서 Modbus를 선택합니다.
- 프로토콜: Standard(일반 시리얼) 또는 Modbus 선택
- 슬레이브 주소: 1~247 (기본: 1)
- 보레이트: 4800 / 9600 / 19200 bps (기본: 9600)
