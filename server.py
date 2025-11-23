import cv2
import threading
from flask import Flask, Response
from flask_cors import CORS
import time
from collections import deque
import numpy as np

app = Flask(__name__)
CORS(app)

# Gestionar múltiples instàncies de càmera
class CameraManager:
    def __init__(self):
        self.clients = deque()
        self.frame = None
        self.lock = threading.Lock()
        self.thread = None
        self.running = False
        
    def start_camera(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._camera_loop)
            self.thread.daemon = True
            self.thread.start()
    
    def stop_camera(self):
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _camera_loop(self):
        cap = cv2.VideoCapture(0)
        backSub = cv2.createBackgroundSubtractorMOG2(200, 16)
        
        while self.running:
            success, frame = cap.read()
            if success:
                with self.lock:
                    self.frame = frame
            time.sleep(0.03)  # ~30 FPS
        
        cap.release()
    
    def get_frame(self, stream_type):
        with self.lock:
            if self.frame is None:
                return None
                
            if stream_type == 'real':
                ret, buffer = cv2.imencode('.jpg', self.frame)
                return buffer.tobytes()
            elif stream_type == 'virtual':
                fg_mask = backSub.apply(self.frame, learningRate=0.7)
                retval, mask_thresh = cv2.threshold(fg_mask, 120, 255, cv2.THRESH_BINARY)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                mask_eroded = cv2.morphologyEx(mask_thresh, cv2.MORPH_OPEN, kernel)
                ret, buffer = cv2.imencode('.jpg', mask_eroded)
                return buffer.tobytes()

# Instància global del gestor de càmera
camera_manager = CameraManager()

def generate_frames(stream_type):
    camera_manager.start_camera()
    
    while True:
        frame_bytes = camera_manager.get_frame(stream_type)
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)

@app.route('/video_feed_real')
def video_feed_real():
    return Response(generate_frames('real'),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_virtual')
def video_feed_virtual():
    return Response(generate_frames('virtual'),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    return "Server is running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)