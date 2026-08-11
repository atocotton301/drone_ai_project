import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import random
import os

try:
    from ultralytics import YOLO
    has_yolo = True
except ImportError:
    has_yolo = False

from tactical_logic import assess_threat_level, assess_danger_zone

class DroneDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("3-OFF Tactical Drone AI Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1E1E1E")
        
        # Load YOLO model
        self.model_path = os.path.join(os.path.dirname(__file__), '..', 'yolov8n.pt')
        if has_yolo and os.path.exists(self.model_path):
            try:
                self.model = YOLO(self.model_path)
            except Exception as e:
                print(f"Error loading YOLO: {e}")
                self.model = None
        else:
            self.model = None
            
        self.cap = cv2.VideoCapture(0) # Use webcam for simulation
        
        self.setup_ui()
        self.update_frame()
        
    def setup_ui(self):
        # Header
        header = tk.Label(self.root, text="ON-DEVICE AI DRONE TACTICAL DASHBOARD", font=("Arial", 24, "bold"), bg="#1E1E1E", fg="#00FF00")
        header.pack(pady=10)
        
        # Main content frame
        main_frame = tk.Frame(self.root, bg="#1E1E1E")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left Panel (Video Feed)
        left_panel = tk.Frame(main_frame, bg="#1E1E1E")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_panel, text="Real-time Vision (YOLOv8)", font=("Arial", 16), bg="#1E1E1E", fg="white").pack()
        self.video_label = tk.Label(left_panel, bg="black")
        self.video_label.pack(pady=10)
        
        # Right Panel (Tactical Map & Logs)
        right_panel = tk.Frame(main_frame, bg="#1E1E1E", width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=20)
        
        # Map
        tk.Label(right_panel, text="SLAM Tactical Map", font=("Arial", 16), bg="#1E1E1E", fg="white").pack()
        self.map_canvas = tk.Canvas(right_panel, width=300, height=300, bg="#2C2C2C", highlightthickness=1, highlightbackground="#00FF00")
        self.map_canvas.pack(pady=10)
        self.draw_map_grid()
        
        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("SYSTEM: ACTIVE | THREAT: LOW | DANGER: SAFE")
        self.status_label = tk.Label(right_panel, textvariable=self.status_var, font=("Arial", 14, "bold"), bg="#1E1E1E", fg="#00FFFF")
        self.status_label.pack(pady=20)
        
        # Log Box
        tk.Label(right_panel, text="System Logs", font=("Arial", 14), bg="#1E1E1E", fg="white").pack(anchor="w")
        self.log_text = tk.Text(right_panel, height=10, width=40, bg="#000000", fg="#00FF00", font=("Consolas", 10))
        self.log_text.pack()
        self.log("System initialized. 3-OFF mode engaged.")
        if not self.model:
            self.log("WARNING: YOLOv8 model not loaded. Running in simulation mode.")
        
    def draw_map_grid(self):
        self.map_canvas.delete("all")
        for i in range(0, 300, 30):
            self.map_canvas.create_line(i, 0, i, 300, fill="#3C3C3C")
            self.map_canvas.create_line(0, i, 300, i, fill="#3C3C3C")
        # Draw drone at center
        self.map_canvas.create_oval(145, 145, 155, 155, fill="#00FF00")
        
    def update_map(self, detections):
        self.draw_map_grid()
        # Mock plotting: if person detected, draw a blue dot on map relative to center
        # For simplicity, just randomly place based on count or specific logic
        # In reality, this would use depth map or SLAM coordinates
        offset = 0
        for d in detections:
            cls = d['class']
            color = "#00FFFF" # person
            if cls == 'weapon': color = "#FF0000"
            if cls == 'fire': color = "#FFA500"
            
            # mock position
            x = 150 + offset
            y = 100 + offset
            self.map_canvas.create_oval(x-5, y-5, x+5, y+5, fill=color)
            self.map_canvas.create_text(x, y-15, text=cls, fill=color)
            offset += 20
        
    def log(self, message):
        t = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{t}] {message}\n")
        self.log_text.see(tk.END)
        
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (640, 480))
            
            detections = []
            if self.model:
                results = self.model(frame, verbose=False)
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        name = self.model.names[cls]
                        conf = float(box.conf[0])
                        detections.append({'class': name, 'bbox': [x1, y1, x2, y2], 'conf': conf})
                        
                        # Draw bbox
                        color = (0, 255, 0)
                        if name in ['weapon', 'fire']: color = (0, 0, 255)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            threat_level, threat_pairs = assess_threat_level(detections)
            danger_level, danger_pairs = assess_danger_zone(detections)
            
            # Update map
            if detections:
                self.update_map(detections)
            
            # Update status
            status_color = "#00FFFF"
            if threat_level == "HIGH" or danger_level == "CRITICAL":
                status_color = "#FF0000"
                if random.random() < 0.05: # Prevent log spam
                    self.log(f"ALERT: Threat {threat_level}, Danger {danger_level}!")
            self.status_var.set(f"SYSTEM: ACTIVE | THREAT: {threat_level} | DANGER: {danger_level}")
            self.status_label.configure(fg=status_color)
            
            # Convert to Tkinter image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
        self.root.after(30, self.update_frame)
        
    def on_closing(self):
        self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DroneDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
