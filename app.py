import cv2
from flask import Flask, render_template
from flask_socketio import SocketIO
from ultralytics import YOLO
import threading
import serial
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CONFIGURAÇÕES ---
MODEL_PATH = 'yolov8n.pt'  
SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600
TOTAL_VAGAS = 32

model = YOLO(MODEL_PATH)

# --- THREAD DO ARDUINO ---
def serial_thread():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Conectado ao Arduino na porta {SERIAL_PORT}")
        while True:
            if ser.in_waiting > 0:
                linha = ser.readline().decode('utf-8', errors='ignore').strip()
                if "ENTRADA" in linha:
                    socketio.emit('evento_arduino', {'tipo': 'entrada', 'msg': 'Carro detectado na cancela!'})
            time.sleep(0.1)
    except Exception as e:
        print("Aviso: Arduino não detectado. O sistema de visão continuará funcionando.")

# --- THREAD DE VISÃO (YOLOv8) ---
def vision_thread():
    cap = cv2.VideoCapture(0)
    
    width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=0.5, verbose=False)  # CORRIGIDO: sem stream=True
        
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                if cls == 2:
                    coords = box.xyxy[0].cpu().numpy()
                    
                    detections.append({
                        'x': (coords[0] / width) * 100,
                        'y': (coords[1] / height) * 100,
                        'w': ((coords[2] - coords[0]) / width) * 100,   # ADICIONADO
                        'h': ((coords[3] - coords[1]) / height) * 100    # ADICIONADO
                    })

        socketio.emit('update_vagas', {
            'ocupadas': len(detections),
            'total': TOTAL_VAGAS,
            'deteccoes': detections
        })

        time.sleep(0.3)

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    t_vision = threading.Thread(target=vision_thread, daemon=True)
    t_serial = threading.Thread(target=serial_thread, daemon=True)
    
    t_vision.start()
    t_serial.start()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)  # CORRIGIDO