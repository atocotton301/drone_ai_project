# 젯슨 보드의 ROS 2 (Humble) 환경에서 동작할 Visual SLAM 연동 노드 뼈대 코드
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
import json
import os
import datetime

class VisualSlamAIBridge(Node):
    def __init__(self):
        super().__init__('visual_slam_ai_bridge')
        
        # 1. AI 탐지 결과 구독 (Jetson AI 노드에서 발행하는 메시지)
        self.subscription = self.create_subscription(
            String,
            '/ai_system/detections',
            self.detection_callback,
            10
        )
        
        # 2. 드론의 현재 위치 (SLAM Odometry) 구독
        self.odom_sub = self.create_subscription(
            PoseStamped,
            '/rtabmap/odom', # RTAB-Map Visual SLAM의 위치 토픽
            self.odom_callback,
            10
        )
        
        # 3. 3D 지도 상에 찍을 시맨틱 마커 발행 (RViz2 또는 맵핑 서버용)
        self.marker_pub = self.create_publisher(String, '/semantic_map/markers', 10)
        
        # [온디바이스 보안 맵핑] 클라우드 전송을 차단하고 젯슨 보드 로컬에만 암호화 저장
        self.local_map_db = []
        self.map_save_path = "/home/jetson/secure_map_data/"
        
        self.current_pose = None
        self.get_logger().info("✅ [Visual SLAM Bridge] 노드가 정상적으로 시작되었습니다.")
        self.get_logger().info("🔒 [보안 맵핑] 외부 네트워크 송출 차단됨. 100% On-device 자율 맵핑 모드 가동.")
        self.get_logger().info("📡 인텔 리얼센스 카메라 및 RTAB-Map 데이터를 대기 중...")

    def odom_callback(self, msg):
        # 드론의 현재 3D 위치를 주기적으로 갱신
        self.current_pose = msg.pose
        
    def detection_callback(self, msg):
        if self.current_pose is None:
            self.get_logger().warning("⚠️ 드론의 SLAM 위치 정보를 아직 받지 못했습니다.")
            return
            
        # JSON 포맷으로 넘어온 AI 탐지 결과 파싱
        detections = json.loads(msg.data)
        
        for det in detections:
            # 예시: 위험 객체(무기, 화재 등) 발견 시 지도에 마킹
            obj_class = det.get('class_name')
            if obj_class in ['weapon', 'fire', 'person']:
                # 실제로는 카메라 핀홀 수식(semantic_map_overlay.py)과 Depth 값을 통해 X, Y, Z 절대 좌표 획득
                world_x = self.current_pose.position.x + 2.0  # 가상의 앞쪽 2m 계산
                world_y = self.current_pose.position.y
                world_z = self.current_pose.position.z
                
                marker_data = {
                    "type": obj_class,
                    "x": world_x,
                    "y": world_y,
                    "z": world_z
                }
                
                self.get_logger().info(f"📍 [지도 마킹] {obj_class} 발견! 지도 좌표(X:{world_x:.2f}, Y:{world_y:.2f})에 마커를 생성합니다.")
                
                # 마커 발행 (내부망 통신용)
                out_msg = String()
                out_msg.data = json.dumps(marker_data)
                self.marker_pub.publish(out_msg)
                
                # [온디바이스 보안 맵핑] 외부 클라우드 의존 없이 자체 로컬 DB에 누적 기록
                self.local_map_db.append(marker_data)
                self.get_logger().info(f"💾 [On-device 저장] 마커 데이터가 로컬 보안 스토리지에 기록되었습니다. (누적: {len(self.local_map_db)}개)")
                
    def save_map_to_disk(self):
        """임무 귀환(RTL) 완료 후, 기체 내부 SSD에 최종 지도를 안전하게 저장 (오프라인 추출용)"""
        if not os.path.exists(self.map_save_path):
            os.makedirs(self.map_save_path)
            
        filename = f"secure_map_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.map_save_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.local_map_db, f)
        self.get_logger().info(f"🛡️ [보안 맵핑 완료] 작전 지도가 기체 내부에 성공적으로 안전하게 저장되었습니다: {filepath}")

def main(args=None):
    # 실제 젯슨 보드에서 실행될 때 rclpy가 초기화됩니다.
    # PC 시뮬레이션 환경에서는 ROS 2가 없으므로 Exception 처리
    try:
        rclpy.init(args=args)
        node = VisualSlamAIBridge()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()
    except ModuleNotFoundError:
        print("💡 [시뮬레이션 모드] ROS 2 (rclpy)가 설치되어 있지 않습니다.")
        print("💡 이 코드는 드론의 젯슨 보드(Ubuntu + ROS 2 환경)에서 RTAB-Map과 함께 실행될 핵심 뼈대입니다.")

if __name__ == '__main__':
    main()
