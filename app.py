import cv2
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import serial
import time

import detectar_service

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CONFIGURAÇÕES ---
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
# Intervalo entre leituras da câmera (segundos)
VISION_INTERVAL = 0.2
total_carros = 0

# --- THREAD DO ARDUINO ---
def serial_thread():
    global total_carros
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Conectado ao Arduino na porta {SERIAL_PORT}")
        while True:
            if ser.in_waiting > 0:
                linha = ser.readline().decode('utf-8', errors='ignore').strip()
                if "ENTRADA" in linha:
                    socketio.emit('evento_arduino', {'tipo': 'entrada', 'msg': 'Carro detectado na cancela!'})
                try:
                    if linha.startswith("ENTRADA:"):
                        valor = int(linha.split(":", 1)[1].strip())
                        total_carros += valor
                        if total_carros < 0:
                            total_carros = 0
                        socketio.emit("contador_carros", {"total": total_carros})
                    elif linha.startswith("SAIDA:"):
                        valor = int(linha.split(":", 1)[1].strip())
                        total_carros -= valor
                        if total_carros < 0:
                            total_carros = 0
                        socketio.emit("contador_carros", {"total": total_carros})
                except (ValueError, IndexError):
                    # Ignora linhas inesperadas da serial sem interromper a thread.
                    pass
            time.sleep(0.1)
    except Exception as e:
        print("Aviso: Arduino não detectado. O sistema de visão continuará funcionando.")

# --- THREAD DE VISÃO (mesma lógica que detectar/sistema_vagas.py) ---
def vision_thread():
    vagas, base_vagas = detectar_service.carregar()
    if vagas is None:
        print(
            "Aviso: não foi possível carregar detectar/vagas.pkl e detectar/base_vagas.pkl. "
            "Execute o fluxo em detectar/sistema_vagas.py (calibrar e salvar base das vagas)."
        )
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Aviso: não foi possível abrir a câmera (índice 0).")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        ids_ocupadas, total = detectar_service.ids_ocupadas_no_frame(
            frame, vagas, base_vagas
        )
        n_ocupadas = len(ids_ocupadas)

        socketio.emit(
            "update_vagas",
            {
                "ocupadas": n_ocupadas,
                "total": total,
                "vagas_ocupadas": ids_ocupadas,
            },
        )

        time.sleep(VISION_INTERVAL)

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    t_vision = threading.Thread(target=vision_thread, daemon=True)
    t_serial = threading.Thread(target=serial_thread, daemon=True)
    
    t_vision.start()
    t_serial.start()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)