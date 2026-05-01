import cv2
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import serial
import time
from database import init_db, registrar_entrada, registrar_saida
modo_diagnostico = False
import detectar_service

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CONFIGURAÇÕES ---
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
VISION_INTERVAL = 0.2
TEMPO_ESTABILIDADE = 5
total_carros = 0

arduino_serial = None
serial_lock = threading.Lock()

# Inicializa o banco de dados
init_db()

def serial_thread():
    global total_carros, arduino_serial
    arduino_serial = None

    DEBUG = False  # 🔥 controle de debug

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(3)
        arduino_serial = ser
        ser.reset_input_buffer()

        print(f"Conectado ao Arduino na porta {SERIAL_PORT}")

        while True:
            linha = ser.readline().decode('utf-8', errors='ignore').strip()

            if not linha:
                continue

            if DEBUG:
                print("SERIAL:", linha)

            # =========================
            # STATUS DIAGNÓSTICO
            # =========================
            if linha.startswith("STATUS:"):
                try:
                    dados_str = linha.replace("STATUS:", "")
                    partes = dados_str.split(";")
                    dados = {}

                    for p in partes:
                        if ":" in p:
                            chave, valor = p.split(":")
                            dados[chave.lower()] = valor

                    socketio.emit("dados_manutencao", dados)

                except Exception as e:
                    print("Erro ao processar STATUS:", e)

                continue

            # =========================
            # SISTEMA NORMAL
            # =========================
            if "ENTRADA" in linha:
                socketio.emit('evento_arduino', {
                    'tipo': 'entrada',
                    'msg': 'Carro detectado na cancela!'
                })

            try:
                if linha.startswith("ENTRADA:"):
                    valor = int(linha.split(":", 1)[1].strip())
                    total_carros += valor
                    total_carros = max(total_carros, 0)

                    socketio.emit("contador_carros", {"total": total_carros})

                elif linha.startswith("SAIDA:"):
                    valor = int(linha.split(":", 1)[1].strip())
                    total_carros -= valor
                    total_carros = max(total_carros, 0)

                    socketio.emit("contador_carros", {"total": total_carros})

            except (ValueError, IndexError):
                pass

    except Exception as e:
        print("❌ ERRO REAL DA SERIAL:", e)

    finally:
        arduino_serial = None

@socketio.on("set_tempo_estabilidade")
def set_tempo_estabilidade(data):
    global TEMPO_ESTABILIDADE
    try:
        t = int((data or {}).get("tempo", TEMPO_ESTABILIDADE))
        if t not in (0, 3, 5, 10):
            t = 5
        TEMPO_ESTABILIDADE = t
        print(f"[CONFIG] Tempo atualizado: {TEMPO_ESTABILIDADE}s")
    except Exception as e:
        print("Erro ao atualizar tempo:", e)


@socketio.on("comando_cancela")
def comando_cancela(data):
    acao = (data or {}).get("acao")
    if acao == "abrir":
        cmd = b"ABRIR_CANCELA\n"
        print("[EMERGENCIA] Forçando abertura da cancela (serial)")
    elif acao == "fechar":
        cmd = b"FECHAR_CANCELA\n"
        print("[EMERGENCIA] Forçando fechamento da cancela (serial)")
    else:
        return
    global arduino_serial
    try:
        if arduino_serial is not None and getattr(arduino_serial, "is_open", False):
            with serial_lock:
                arduino_serial.write(cmd)
                arduino_serial.flush()
        else:
            print("Aviso: Arduino não conectado — comando da cancela não enviado.")
    except Exception as e:
        print("Erro ao enviar comando da cancela:", e)

@socketio.on("start_diag")
def start_diag():
    global arduino_serial
    print("[DIAG] Iniciando modo diagnóstico")

    try:
        if arduino_serial is not None and arduino_serial.is_open:
            with serial_lock:
                arduino_serial.write(b"START_DIAG\n")
                arduino_serial.flush()
    except Exception as e:
        print("Erro ao iniciar diagnóstico:", e)


@socketio.on("stop_diag")
def stop_diag():
    global arduino_serial
    print("[DIAG] Parando modo diagnóstico")

    try:
        if arduino_serial is not None and arduino_serial.is_open:
            with serial_lock:
                arduino_serial.write(b"STOP_DIAG\n")
                arduino_serial.flush()
    except Exception as e:
        print("Erro ao parar diagnóstico:", e)

# --- THREAD DE VISÃO ---
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

    estado_real  = [False] * total
    estado_temp  = [False] * total
    tempo_inicio = [None]  * total

    # Controle para detectar entradas e saídas por vaga
    vagas_anteriores = set()

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
        te = max(0, TEMPO_ESTABILIDADE)

        for i in range(total):
            det = estado_detectado[i]
            if det != estado_temp[i]:
                estado_temp[i] = det
                tempo_inicio[i] = agora
            elif tempo_inicio[i] is not None and (agora - tempo_inicio[i]) >= te:
                estado_real[i] = estado_temp[i]

        ids_confirmadas = [
            i + 1 for i, ocupado in enumerate(estado_real) if ocupado
        ]

        # --- DETECÇÃO DE ENTRADAS E SAÍDAS POR VAGA ---
        conjunto_atual    = set(ids_confirmadas)
        novas_entradas    = conjunto_atual - vagas_anteriores
        novas_saidas      = vagas_anteriores - conjunto_atual

        for vaga in novas_entradas:
            registrar_entrada(vaga)

        for vaga in novas_saidas:
            registrar_saida(vaga)

        vagas_anteriores = conjunto_atual

        socketio.emit(
            "update_vagas",
            {
                "ocupadas"     : len(ids_confirmadas),
                "total"        : total,
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

    socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)