# ENV130 (C1D-330) 데이터 및 통신 설정 가이드

## 데이터 저장
- 저장 간격: 1초/10초/1분(기본)/10분/1시간
- 다운로드: 시리얼 포트
- 삭제: 복구 불가

## 파형 저장
- 모드: Real / Average(기본)
- 간격: 1초/10초/1분(기본)/10분/1시간

## 통신 설정
### Modbus
- 보레이트: 9600/19200(기본)/115200
- 슬레이브 주소: 1~255 (기본: 1)

### RF 통신
- 할당: Light/Heavy(기본)
- 주소: 1~4 (기본: 1)

## 메뉴 구조 (공개 섹션)
```
├── 측정 (Measurement) - Base, Calibration
├── 출력 (Output) - Current, Relay, Clean, Error
├── 데이터 (Data) - Trend, Communication, Echo
└── 시스템 (System) - Passcode, Language, Time, Site Name, Factory Reset
```
