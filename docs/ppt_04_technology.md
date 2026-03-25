# ENV200 계측 기술 가이드

## EEA (Energy Envelope Average)
- 초음파 에코 신호의 에너지 포락선 평균을 계산하는 WESS 고유 기술
- 일반 초음파 감쇠법보다 안정적이고 정확한 농도 측정 가능

## 농도 (Density)
- 농도: 용액을 구성하는 성분의 양의 정도
- 밀도: 단위 부피당 질량
- 표현 방식: Weight Per Weight(%) 또는 Weight Per Volume(mg/L, g/L)

## AGC (Auto Gain Control)
- 수신 감도를 자동으로 조절하여 최적의 에코 신호를 확보하는 기능

## 측정 시퀀스
1. 초음파 발사
2. 에코 신호 수신
3. 신호 증폭(AGC)
4. 프로파일 축적
5. EEA 계산
6. 교정(Calibration) 적용
7. 최종 농도값 출력

## Echo Screen
- Time Domain 방식으로 에코 파형을 실시간 표시
- 검출 범위(Detection Area), 임계값(Threshold) 등 확인 가능
- 파라미터 화면에서 현재 설정값 확인

## Calibration (교정)

### 개념
- EEA값과 실제 농도(Density) 간의 관계를 설정하는 과정
- Zero(영점), Point 1, Point 2 등 기준점으로 보정

### 교정 절차
1. 기준 시료(알려진 농도) 준비
2. 영점(Zero) 교정 실행
3. 스팬(Span) 교정 실행
4. 교정 완료 후 측정 시작

## Damping (댐핑)
- 출력값의 급격한 변동을 억제하는 이동평균 필터
- 값이 크면 안정적이지만 응답이 느림
- 값이 작으면 빠르지만 변동이 큼

## Offset (오프셋)
- 측정값에 일정 보정값을 더하거나 빼는 기능
- 예: 실제 농도가 1.0%인데 0.9%로 표시되면 오프셋 +0.1 설정
