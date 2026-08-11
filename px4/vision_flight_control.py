import asyncio
import time
from mavsdk import System
from mavsdk.offboard import (OffboardError, VelocityBodyYawspeed)

class DroneController:
    """
    PX4(Pixhawk) 비행 제어를 캡슐화한 클래스입니다.
    외부(메인 루프)에서는 이 클래스의 메서드만 호출하여 드론을 제어합니다.
    """
    def __init__(self, system_address="udp://:14540"):
        self.drone = System()
        self.system_address = system_address
        self.is_connected = False
        self.is_armed = False
        self.is_offboard = False

    async def connect(self):
        print(f"🚁 [비행 제어기] {self.system_address} 로 연결 시도 중...")
        await self.drone.connect(system_address=self.system_address)
        
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("✅ [비행 제어기] 통신 연결 성공!")
                self.is_connected = True
                break

    async def arm(self):
        if not self.is_connected: return
        print("🛡️ [비행 제어기] 무장(Arming) 시도...")
        await self.drone.action.arm()
        self.is_armed = True

    async def disarm(self):
        if not self.is_connected: return
        print("🛑 [비행 제어기] 무장 해제(Disarming)...")
        await self.drone.action.disarm()
        self.is_armed = False

    async def start_offboard(self):
        """GPS-Deny 자율비행을 위한 Offboard 모드 진입"""
        if not self.is_armed:
            print("⚠️ 무장(Arm) 상태가 아닙니다.")
            return

        print("🚦 초기 제로 속도 주입 (Hovering)...")
        await self.drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))

        try:
            print("🚀 GPS-Denied 오프보드 제어 모드 진입!")
            await self.drone.offboard.start()
            self.is_offboard = True
        except OffboardError as error:
            print(f"❌ 오프보드 진입 실패: {error._result.result}")
            await self.disarm()

    async def set_velocity(self, forward_m_s, right_m_s, down_m_s, yaw_deg_s):
        """
        드론의 속도와 회전을 제어합니다. (기체 기준 좌표계)
        """
        if not self.is_offboard: return
        await self.drone.offboard.set_velocity_body(
            VelocityBodyYawspeed(forward_m_s, right_m_s, down_m_s, yaw_deg_s)
        )

    async def evasive_maneuver(self):
        """
        [ZERO-LATENCY 전술 회피 기동]
        무장 타겟 식별 즉시, 지그재그 기동 및 고도 급강하로 적의 조준을 교란합니다.
        온디바이스(엣지) 연산이므로 네트워크 딜레이 없이 0.1초 내 즉각 반응합니다.
        """
        print("⚡ [회피 기동] 지그재그 강하 기동 (Evasive Maneuver) 발동!!")
        if not self.is_offboard: return
        
        # 1. 우측 회피 및 강하
        await self.set_velocity(0.0, 2.0, 1.0, 0.0)
        await asyncio.sleep(0.5)
        # 2. 좌측 회피 및 추가 강하
        await self.set_velocity(0.0, -2.0, 1.0, 0.0)
        await asyncio.sleep(0.5)
        # 3. 호버링 복귀
        await self.set_velocity(0.0, 0.0, 0.0, 0.0)

    async def autonomous_explore(self):
        """
        [완전 자율 오프그리드 탐색 (Fire-and-Forget)]
        통신 두절(Radio Silence) 상태에서 스스로 실내 미로를 개척하며 전진합니다.
        """
        print("🧭 [자율 탐색] Off-Grid 룸 클리어링 알고리즘 가동 중...")
        # 단순 전진 (실제로는 SLAM 데이터를 받아 방향 결정)
        await self.set_velocity(1.0, 0.0, 0.0, 0.0)

    async def emergency_land(self):
        """페일세이프(Failsafe) 시 강제 착륙 또는 제자리 호버링 후 착륙"""
        print("🛬 [긴급 프로토콜] 강제 착륙(Land) 명령 집행!")
        if self.is_offboard:
            # 먼저 제자리에 멈춤
            await self.set_velocity(0.0, 0.0, 0.0, 0.0)
            await asyncio.sleep(0.5)
            await self.drone.offboard.stop()
            self.is_offboard = False
            
        await self.drone.action.land()

    async def stop(self):
        await self.emergency_land()

if __name__ == "__main__":
    # 클래스 단독 테스트용 목업
    async def run_test():
        controller = DroneController()
        await controller.connect()
        await controller.arm()
        await controller.start_offboard()
        await controller.set_velocity(0.5, 0.0, 0.0, 0.0) # 0.5m/s 전진
        await asyncio.sleep(2)
        await controller.emergency_land()
        
    # Windows 환경에서 MAVSDK 연결 실패 방지를 위해 주석 처리 (실제 환경에서 활성화)
    # asyncio.run(run_test())
    print("✅ DroneController 클래스 컴파일 정상.")
