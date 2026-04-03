"""
Lê calibração em detectar/ (vagas.pkl + base_vagas.pkl) e calcula
ocupação por vaga no mesmo critério de detectar/sistema_vagas.monitorar().
"""
import os
import pickle

import cv2
import numpy as np

_DIR = os.path.dirname(os.path.abspath(__file__))
_DETECTAR = os.path.join(_DIR, "detectar")
ARQUIVO_VAGAS = os.path.join(_DETECTAR, "vagas.pkl")
BASE_VAGAS = os.path.join(_DETECTAR, "base_vagas.pkl")

LIMIAR = 50

def carregar():
    """Retorna (lista_vagas, base_vagas) ou (None, None) se faltar ficheiro."""
    if not os.path.exists(ARQUIVO_VAGAS) or not os.path.exists(BASE_VAGAS):
        return None, None
    with open(ARQUIVO_VAGAS, "rb") as f:
        vagas = pickle.load(f)
    with open(BASE_VAGAS, "rb") as f:
        base_vagas = pickle.load(f)
    if len(vagas) != len(base_vagas):
        return None, None
    return vagas, base_vagas


def ids_ocupadas_no_frame(frame, vagas, base_vagas, limiar=LIMIAR):
    """
    Índice da vaga i (0-based) corresponde ao número mostrado no app: i + 1.
    Retorna lista de inteiros [1..N] das vagas ocupadas e o total de vagas.
    """
    ocupadas_ids = []
    for i, vaga in enumerate(vagas):
        pts = np.array(vaga["pontos"], np.int32)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [pts], 255)
        vaga_atual = cv2.bitwise_and(frame, frame, mask=mask)
        x, y, w, h = cv2.boundingRect(pts)
        corte_atual = vaga_atual[y : y + h, x : x + w]
        base = base_vagas[i]
        if corte_atual.size == 0 or base.size == 0:
            continue

        corte_atual = cv2.resize(corte_atual, (base.shape[1], base.shape[0]))        
        dif = cv2.absdiff(base, corte_atual)       
        gray = cv2.cvtColor(dif, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)        
        _, thresh = cv2.threshold(blur, limiar, 255, cv2.THRESH_BINARY)        
        media = np.mean(thresh)        
        if media > limiar:
            ocupadas_ids.append(i + 1)
    return ocupadas_ids, len(vagas)
