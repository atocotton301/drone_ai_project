# 3-OFF 방산용 드론 하드웨어 조립 및 PX4 세팅 가이드 (Week 1)

이 문서는 실물 드론 제작 1주차 목표인 **"하드웨어 조립 및 오프라인(GPS-OFF) 비행 준비"**를 위한 상세 가이드입니다.

## 1. 하드웨어 구성 부품 (BOM)
- **프레임 (Frame):** Holybro X500 V2
- **비행 제어기 (FCC):** Holybro Pixhawk 6C
- **임무 컴퓨터 (Companion Computer):** NVIDIA Jetson Orin Nano Super
- **비전 센서 (Vision Sensor):** Intel RealSense D435i
- **보조 항법 센서 (Optical Flow & Lidar):** Holybro H-Flow 센서 (GPS 단절 환경 필수)
- **전원 분배 (Power):** 4S ~ 6S Lipo 배터리 및 5V/3A 듀얼 BEC (Jetson 전원용)

## 2. 하드웨어 조립 순서 (Hardware Assembly)
1. **프레임 및 모터 결합:** X500 V2 매뉴얼에 따라 모터와 ESC(변속기)를 암대에 결합합니다. 방위(CW, CCW)에 유의하십시오.
2. **Pixhawk 6C 마운팅:** 기체 정중앙(무게 중심)에 진동 방지 패드를 대고 Pixhawk 6C를 화살표 방향(전방)에 맞춰 부착합니다.
3. **Jetson Orin Nano 마운팅:** Pixhawk 상단 플레이트 혹은 하단 배터리 베이 위쪽의 빈 공간에 카본/아크릴 플레이트를 덧대어 Jetson을 볼트로 단단히 고정합니다. (통풍을 위한 팬 여유 공간 확보)
4. **H-Flow 센서 부착:** 기체 하단(지면을 바라보게)에 부착합니다. 렌즈가 깨끗한지 확인하고 Pixhawk의 `I2C` 또는 `TELEM` 포트(매뉴얼 핀맵 참조)에 연결합니다.
5. **RealSense D435i 부착:** 기체 전방(수평 혹은 15도 하향)에 3D 프린팅 마운트를 이용해 장착합니다. USB 3.0 케이블은 Jetson과 연결합니다.

## 3. 전원 및 배선 (Wiring & Power)
> [!CAUTION]
> Jetson 보드는 전압 민감도가 높습니다. 반드시 배터리 직결이 아닌 **BEC(전압 강하 모듈, 5V/4A 이상 권장)**를 통해 전원을 인가해야 보드 손상을 막을 수 있습니다.

- **Pixhawk 전원:** 기본 제공되는 Power Module(PM02)을 통해 배터리 전원을 공급합니다.
- **Jetson 전원:** 배터리 라인에서 분기(Y-cable)하여 BEC를 거쳐 Jetson의 잭(또는 배럴 커넥터)으로 5V(또는 보드 허용 전압)를 공급합니다.
- **텔레메트리 연동 (FCC <-> Jetson):** Pixhawk의 `TELEM2` 포트를 Jetson의 UART(GPIO 핀) 또는 USB(FTDI 케이블)에 연결합니다. 이 라인이 ROS2 통신의 핵심 척추가 됩니다.

## 4. PX4 펌웨어 세팅 및 캘리브레이션
1. **펌웨어 플래싱:** QGroundControl(QGC)을 PC에 설치하고 Pixhawk를 USB로 연결합니다. 최신 **PX4 Autopilot Stable Release**를 플래싱합니다.
2. **기본 캘리브레이션:** 평평한 곳에서 `센서` 탭을 열고 가속도계, 자이로스코프, 지자기(Compass) 캘리브레이션을 진행합니다.
3. **기체 프레임 설정:** `Airframe` 탭에서 `Holybro X500 V2` (Quadrotor X)를 선택하고 재부팅합니다.

## 5. 3-OFF (GPS-OFF) 비행을 위한 필수 파라미터 세팅
GPS가 끊긴 밀폐 공간에서 H-Flow 센서만으로 제자리 비행(Position Hold)을 하려면 다음 파라미터를 QGC에서 변경해야 합니다.

* `SENS_FLOW_ROT`: H-Flow 장착 방향에 맞게 설정 (보통 0 또는 8).
* `EKF2_OF_CTRL`: `1` (Optical Flow 데이터 융합 활성화).
* `EKF2_RNG_CTRL`: `1` (거리 센서 데이터 융합 활성화).
* `EKF2_HGT_MODE`: `2` (Range finder 기반 고도 추정 우선).
* `EKF2_GPS_CTRL`: `0` (비상시를 위해 GPS 데이터 융합 끄기 - 완전한 오프라인 테스트용).

세팅 후 기체를 손으로 들고 움직였을 때 QGC 화면의 고도와 속도 데이터가 정상적으로 튀는지(반응하는지) 확인합니다.

---
**다음 단계(2주차):** Jetson 내부에 ROS 2를 설치하고 이 Pixhawk와 통신할 수 있는 `MicroXRCE-DDS` 브릿지를 구축합니다.
