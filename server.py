import cv2
import threading
from flask import Flask, Response
from flask_cors import CORS
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class CameraSystem:
    def __init__(self):
        self.cap = None
        self.backSub = cv2.createBackgroundSubtractorMOG2(200, 16)
        self.latest_frame_real = None
        self.latest_frame_virtual = None
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.client_count = 0
        self.client_lock = threading.Lock()
    
    def start_camera(self):
        with self.client_lock:
            self.client_count += 1
            logger.info(f"Cliente conectado. Total: {self.client_count}")
            
            if self.client_count == 1 and not self.running:
                self.running = True
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    logger.error("No se pudo abrir la cámara")
                    # Intentar con índice 1 si 0 falla
                    self.cap = cv2.VideoCapture(1)
                    if not self.cap.isOpened():
                        logger.error("No se pudo abrir ninguna cámara")
                        return False
                
                self.thread = threading.Thread(target=self._update_frames)
                self.thread.daemon = True
                self.thread.start()
                logger.info("Cámara iniciada")
        
        return True
    
    def stop_camera(self):
        with self.client_lock:
            self.client_count -= 1
            logger.info(f"Cliente desconectado. Total: {self.client_count}")
            
            if self.client_count <= 0 and self.running:
                self.running = False
                if self.cap and self.cap.isOpened():
                    self.cap.release()
                if self.thread:
                    self.thread.join(timeout=2.0)
                logger.info("Cámara detenida")
    
    def _update_frames(self):
        while self.running:
            success, frame = self.cap.read()
            if success:
                # Frame real
                _, buffer_real = cv2.imencode('.jpg', frame)
                frame_real = buffer_real.tobytes()
                
                # Frame virtual
                fg_mask = self.backSub.apply(frame, learningRate=0.7)
                _, mask_thresh = cv2.threshold(fg_mask, 120, 255, cv2.THRESH_BINARY)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                mask_eroded = cv2.morphologyEx(mask_thresh, cv2.MORPH_OPEN, kernel)
                _, buffer_virtual = cv2.imencode('.jpg', mask_eroded)
                frame_virtual = buffer_virtual.tobytes()
                
                with self.lock:
                    self.latest_frame_real = frame_real
                    self.latest_frame_virtual = frame_virtual
            else:
                logger.error("Error leyendo frame de la cámara")
                # Crear frame negro como fallback
                black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                _, buffer = cv2.imencode('.jpg', black_frame)
                frame_bytes = buffer.tobytes()
                with self.lock:
                    self.latest_frame_real = frame_bytes
                    self.latest_frame_virtual = frame_bytes
                time.sleep(0.1)
            
            time.sleep(0.033)  # ~30 FPS
    
    def get_frame(self, frame_type):
        with self.lock:
            if frame_type == 'real':
                return self.latest_frame_real
            elif frame_type == 'virtual':
                return self.latest_frame_virtual
        return None

# Instancia global del sistema de cámara
camera_system = CameraSystem()

def generate_frames(frame_type):
    # Iniciar cámara para este cliente
    if not camera_system.start_camera():
        # Si no se pudo iniciar la cámara, enviar frame negro
        black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', black_frame)
        frame_bytes = buffer.tobytes()
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.033)
    
    try:
        while True:
            frame_bytes = camera_system.get_frame(frame_type)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Frame vacío mientras se inicia la cámara
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
            time.sleep(0.033)
    except GeneratorExit:
        # Cliente desconectado
        camera_system.stop_camera()
        raise

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
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)