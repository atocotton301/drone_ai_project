import cv2
import numpy as np

try:
    import pyrealsense2 as rs
    REALSENSE_AVAILABLE = True
except ImportError:
    REALSENSE_AVAILABLE = False
    print("⚠️ [RealSense] pyrealsense2 라이브러리가 설치되지 않았습니다. 일반 웹캠 모드로 폴백(Fallback) 합니다.")

class RealSenseDriver:
    """
    Intel RealSense D435i 하드웨어 카메라와 통신하여
    RGB(컬러) 이미지와 Depth(깊이) 이미지를 실시간으로 받아오는 드라이버입니다.
    """
    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.is_connected = False
        self.use_realsense = False
        self.cap = None
        
        if REALSENSE_AVAILABLE:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            
            # RGB 및 Depth 스트림 활성화
            self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
            self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
            
            # 깊이 이미지와 컬러 이미지의 시점을 일치시키기 위한 Align 객체
            self.align = rs.align(rs.stream.color)

    def start(self):
        print("📷 [Camera] 카메라 스트리밍 시작 시도...")
        if REALSENSE_AVAILABLE:
            try:
                self.profile = self.pipeline.start(self.config)
                # 깊이 센서의 1 픽셀 값이 실제 미터(m)로 얼마인지 추출
                depth_sensor = self.profile.get_device().first_depth_sensor()
                self.depth_scale = depth_sensor.get_depth_scale()
                self.is_connected = True
                self.use_realsense = True
                print("✅ [RealSense] D435i 정상 연결 및 활성화 완료.")
                return
            except Exception as e:
                print(f"❌ [RealSense] 연결 실패! 일반 웹캠으로 폴백합니다. 에러: {e}")
                
        # 리얼센스 패키지가 없거나 연결에 실패한 경우 웹캠 폴백
        self.use_realsense = False
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
        if self.cap.isOpened():
            self.is_connected = True
            print("✅ [Webcam Fallback] 일반 웹캠 0번 활성화 완료.")
        else:
            self.is_connected = False
            print("❌ [Webcam] 일반 웹캠 0번 연결에도 실패했습니다.")

    def get_frames(self):
        """
        RGB 프레임과 Depth 프레임을 반환합니다.
        반환값: (rgb_frame, depth_frame_in_meters)
        """
        if not self.is_connected:
            return None, None

        if self.use_realsense:
            try:
                frames = self.pipeline.wait_for_frames(timeout_ms=2000)
                aligned_frames = self.align.process(frames)
            except Exception as e:
                print(f"⚠️ [RealSense] 프레임 수신 대기 초과 (연결 끊김 의심): {e}")
                self.is_connected = False
                return None, None
            
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                return None, None
                
            # OpenCV에서 쓸 수 있게 numpy 배열로 변환
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            # 원시 depth 데이터(uint16)를 미터(m) 단위 32비트 실수(float32)로 변환
            # 중간 메모리 생성(float64)을 방지하기 위해 dtype=np.float32를 명시
            depth_in_meters = np.multiply(depth_image, self.depth_scale, dtype=np.float32)
            
            return color_image, depth_in_meters
        else:
            ret, frame = self.cap.read()
            if not ret: return None, None
            # 일반 웹캠은 깊이 정보가 없으므로 0으로 채워진 가짜 뎁스맵 반환 (float32)
            frame = cv2.resize(frame, (self.width, self.height))
            fake_depth = np.zeros((self.height, self.width), dtype=np.float32)
            return frame, fake_depth

    def stop(self):
        print("🛑 [Camera] 스트리밍 종료.")
        if self.use_realsense and self.is_connected:
            try:
                self.pipeline.stop()
            except Exception:
                pass
        elif self.cap and self.cap.isOpened():
            self.cap.release()
        self.is_connected = False
            
if __name__ == "__main__":
    # 단독 테스트 코드
    cam = RealSenseDriver()
    cam.start()
    if cam.is_connected:
        print("테스트 프레임 수신 중... (Ctrl+C로 종료)")
        try:
            while True:
                color, depth = cam.get_frames()
                if color is not None:
                    # 중심점의 깊이(거리) 출력
                    h, w = depth.shape
                    center_dist = depth[h//2, w//2]
                    
                    # 깊이 맵 시각화 (가짜 컬러)
                    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth, alpha=255/3.0), cv2.COLORMAP_JET)
                    
                    # 영상 출력
                    cv2.putText(color, f"Center Dist: {center_dist:.2f}m", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow('RGB', color)
                    cv2.imshow('Depth', depth_colormap)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        except KeyboardInterrupt:
            pass
        finally:
            cam.stop()
            cv2.destroyAllWindows()
