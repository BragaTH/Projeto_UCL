import cv2
import pickle
import numpy as np
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_VAGAS = os.path.join(_DIR, "vagas.pkl")
BASE_VAGAS = os.path.join(_DIR, "base_vagas.pkl")
BASE_JPG = os.path.join(_DIR, "base.jpg")

# ==========================
# CAPTURAR BASE
# ==========================
def capturar_base():
    cap = cv2.VideoCapture(0)

    print("Pressione 'c' para capturar base | 'q' para sair")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Captura Base", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            cv2.imwrite(BASE_JPG, frame)
            print("Base capturada!")
            break

        elif key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# ==========================
# CALIBRAÇÃO
# ==========================
vagas = []
pontos = []

def clique(event, x, y, flags, param):
    global pontos, vagas

    if event == cv2.EVENT_LBUTTONDOWN:

        if len(vagas) >= 24:
            print("⚠️ Limite de 24 vagas atingido!")
            return

        pontos.append((x,y))

        if len(pontos) == 4:
            nome = f"Vg{len(vagas)+1}"

            vaga = {
                "id": nome,
                "pontos": pontos.copy()
            }

            vagas.append(vaga)
            print(f"✅ {nome} criada!")
            pontos.clear()

def calibrar():
    global vagas, pontos

    img = cv2.imread(BASE_JPG)

    if img is None:
        print("Capture a base primeiro")
        return

    cv2.namedWindow("Calibracao")
    cv2.setMouseCallback("Calibracao", clique)

    print("Clique 4 pontos por vaga (máx 24)")
    print("s = salvar | q = sair")

    while True:
        frame = img.copy()

        for vaga in vagas:
            pts = np.array(vaga["pontos"], np.int32)
            cv2.polylines(frame, [pts], True, (0,255,0), 2)

            nome = vaga["id"]
            cx = int(np.mean(pts[:,0]))
            cy = int(np.mean(pts[:,1]))
            cv2.putText(frame, nome, (cx, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

        for p in pontos:
            cv2.circle(frame, p, 5, (0,0,255), -1)

        cv2.imshow("Calibracao", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            with open(ARQUIVO_VAGAS, "wb") as f:
                pickle.dump(vagas, f)

            print(f"✅ {len(vagas)} vagas salvas!")
            break

        elif key == ord('q') or key == 27:
            break

    cv2.destroyAllWindows()


# ==========================
# SALVAR BASE DAS VAGAS
# ==========================
def salvar_base_vagas():
    if not os.path.exists(ARQUIVO_VAGAS):
        print("Calibre primeiro")
        return

    img = cv2.imread(BASE_JPG)

    with open(ARQUIVO_VAGAS, "rb") as f:
        vagas = pickle.load(f)

    base_vagas = []

    for vaga in vagas:
        pts = np.array(vaga["pontos"], np.int32)

        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [pts], 255)

        vaga_img = cv2.bitwise_and(img, img, mask=mask)

        x,y,w,h = cv2.boundingRect(pts)
        corte = vaga_img[y:y+h, x:x+w]

        base_vagas.append(corte)

    with open(BASE_VAGAS, "wb") as f:
        pickle.dump(base_vagas, f)

    print("Base das vagas salva!")


# ==========================
# MONITORAMENTO
# ==========================
def monitorar():

    if not os.path.exists(BASE_VAGAS):
        print("Execute salvar_base_vagas primeiro")
        return

    with open(ARQUIVO_VAGAS, "rb") as f:
        vagas = pickle.load(f)

    with open(BASE_VAGAS, "rb") as f:
        base_vagas = pickle.load(f)

    estado = [0]*len(vagas)

    cap = cv2.VideoCapture(0)

    LIMIAR = 25

    print("Monitorando... (q ou ESC para sair)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        ocupadas = 0

        for i, vaga in enumerate(vagas):
            pts = np.array(vaga["pontos"], np.int32)
            nome = vaga["id"]

            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [pts], 255)

            vaga_atual = cv2.bitwise_and(frame, frame, mask=mask)

            x,y,w,h = cv2.boundingRect(pts)
            corte_atual = vaga_atual[y:y+h, x:x+w]

            base = base_vagas[i]
            corte_atual = cv2.resize(corte_atual, (base.shape[1], base.shape[0]))

            dif = cv2.absdiff(base, corte_atual)
            media = np.mean(dif)

            ocupada = media > LIMIAR

            # 🔹 DETECÇÃO DE EVENTO
            if estado[i] == 0 and ocupada:
                print(f"🚗 Entrou na {nome}")

            if estado[i] == 1 and not ocupada:
                print(f"🚗 Saiu da {nome}")

            estado[i] = 1 if ocupada else 0

            if ocupada:
                ocupadas += 1

            # Marcações das vagas sobre o vídeo (como na calibração)
            cor_borda = (0, 0, 255) if ocupada else (0, 255, 0)
            cv2.polylines(frame, [pts], True, cor_borda, 2)
            cx = int(np.mean(pts[:, 0]))
            cy = int(np.mean(pts[:, 1]))
            cv2.putText(
                frame,
                nome,
                (cx, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                cor_borda,
                2,
            )

        livres = len(vagas) - ocupadas

        # 🔹 PAINEL
        cv2.rectangle(frame, (0,0), (350,120), (0,0,0), -1)

        cv2.putText(frame, f"LIVRES: {livres}", (10,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        cv2.putText(frame, f"OCUPADAS: {ocupadas}", (10,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        # 🚨 LOTADO
        if ocupadas == len(vagas):
            cv2.putText(frame, "ESTACIONAMENTO LOTADO", (50,200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0,0,255), 3)

        cv2.imshow("Sistema Maquete", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# ==========================
# MENU
# ==========================
def menu():
    while True:
        print("\n1 - Capturar base")
        print("2 - Calibrar vagas")
        print("3 - Salvar base das vagas")
        print("4 - Monitorar")
        print("5 - Sair")

        op = input("Escolha: ")

        if op == "1":
            capturar_base()
        elif op == "2":
            calibrar()
        elif op == "3":
            salvar_base_vagas()
        elif op == "4":
            monitorar()
        elif op == "5":
            break

if __name__ == "__main__":
    menu()
