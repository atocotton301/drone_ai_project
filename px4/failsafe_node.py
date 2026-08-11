import time
import threading

class TacticalFailsafeNode:
    def __init__(self, timeout_limit_sec=0.5):
        self.timeout_limit_sec = timeout_limit_sec
        self.last_heartbeat_time = time.time()
        self.is_running = True
        
    def receive_camera_heartbeat(self):
        """카메라 등 필수 하드웨어 센서의 정상 동작(Heartbeat) 수신"""
        self.last_heartbeat_time = time.time()
        
    def timeout_interrupt_isr(self):
        """
        [하드웨어 센서 장애 페일세이프(Failsafe) 구현부]
        시각 센서(카메라)가 망가지거나 프레임 드롭이 심하게 발생하면, 
        더 이상 자율 비행이 불가능하므로 이를 즉각 감지합니다. (네트워크 핑 감시 아님)
        """
        print(f"🛡️ [Failsafe] 하드웨어(카메라) 센서 장애 감시 가동 (허용 지연: {self.timeout_limit_sec}초)")
        
        while self.is_running:
            time_elapsed = time.time() - self.last_heartbeat_time
            
            # 지정된 시간 내에 신호가 오지 않으면 즉시 예외 상황(TimeOut)으로 판단
            if time_elapsed > self.timeout_limit_sec:
                print(f"\n🚨 [치명적 에러!] {time_elapsed:.2f}초간 시각 센서(카메라) 프레임 수신 실패.")
                self.trigger_emergency_protocol()
                break
                
            time.sleep(0.05) # 50ms 간격으로 엄격히 감시
            
    def trigger_emergency_protocol(self):
        """
        """
        print("⚠️ [하드웨어 페일세이프] 눈(카메라)이 멀었습니다. 즉각 제어권 회수 및 강제 호버링 집행!")
        print("🚁 [전술 장비 생존성 확보] 안전 구역으로 강제 귀환(RTL) 모드로 전환합니다.")
        # 추후 MAVSDK의 drone.action.return_to_launch() 등 실제 코드가 연동될 위치
        self.is_running = False

if __name__ == "__main__":
    # 독립된 모듈 테스트
    failsafe_system = TacticalFailsafeNode(timeout_limit_sec=1.0)
    
    # 인터럽트 감시 스레드를 백그라운드에서 실행
    monitor_thread = threading.Thread(target=failsafe_system.timeout_interrupt_isr)
    monitor_thread.start()
    
    # 1. 정상 센서 작동 상황 모사
    for i in range(3):
        print("🎥 [센서] 카메라 프레임 정상 수신 중 (Heartbeat)")
        failsafe_system.receive_camera_heartbeat()
        time.sleep(0.5)
        
    # 2. 적의 공격으로 카메라가 파손된 상황 모사 (1초 이상 프레임 없음)
    print("\n💥 [적대적 환경] 기체 피격으로 인한 카메라 센서 파손 모사! 눈이 멉니다...")
    time.sleep(2.0)
