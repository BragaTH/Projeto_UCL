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
# Estabilidade temporal (segundos) — atualizável via Socket.IO sem reiniciar
TEMPO_ESTABILIDADE = 5
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


@socketio.on("set_tempo_estabilidade")
def set_tempo_estabilidade(data):
    global TEMPO_ESTABILIDADE
    try:
        t = int((data or {}).get("tempo", TEMPO_ESTABILIDADE))
        if t not in (3, 5, 8, 10):
            t = 5
        TEMPO_ESTABILIDADE = t
        print(f"[CONFIG] Tempo atualizado: {TEMPO_ESTABILIDADE}s")
    except Exception as e:
        print("Erro ao atualizar tempo:", e)


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

    total = len(vagas)

    # Estado confirmado (emitido ao front) vs. leitura instantânea da deteção
    estado_real = [False] * total
    estado_temp = [False] * total
    tempo_inicio = [None] * total  # time.monotonic() quando estado_temp mudou

    print("Visão com estabilidade temporal ativa (ajustável em tempo real).")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        ids_ocupadas, _ = detectar_service.ids_ocupadas_no_frame(
            frame, vagas, base_vagas
        )

        estado_detectado = [False] * total
        for idx in ids_ocupadas:
            if 1 <= idx <= total:
                estado_detectado[idx - 1] = True

        agora = time.monotonic()
        te = TEMPO_ESTABILIDADE
        if te < 1:
            te = 1

        for i in range(total):
            det = estado_detectado[i]
            if det != estado_temp[i]:
                estado_temp[i] = det
                tempo_inicio[i] = agora
            elif tempo_inicio[i] is not None and (agora - tempo_inicio[i]) >= te:
                estado_real[i] = estado_temp[i]

        # 🔹 Monta lista final confirmada
        ids_confirmadas = [
            i + 1 for i, ocupado in enumerate(estado_real) if ocupado
        ]

        socketio.emit(
            "update_vagas",
            {
                "ocupadas": len(ids_confirmadas),
                "total": total,
                "vagas_ocupadas": ids_confirmadas,
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
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)  # CORRIGIDO