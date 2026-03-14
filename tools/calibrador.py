import cv2

<<<<<<< HEAD
CAMINHO_IMAGEM = 'static/img/estacionamento.png'
=======
CAMINHO_IMAGEM = 'static/img/Maquete.jpeg'
>>>>>>> d661233e861b7b893b511f20007df4d8bc768a6d

vagas_coordenadas = []

def clique_mouse(event, x, y, flags, param):

    if event == cv2.EVENT_LBUTTONDOWN:

        altura_img, largura_img = img_exibicao.shape[:2]

        left = round((x / largura_img) * 100, 2)
        top = round((y / altura_img) * 100, 2)

        vagas_coordenadas.append((top, left))
        proxima_vaga = len(vagas_coordenadas)

        cv2.circle(img_exibicao, (x, y), 5, (0,255,0), -1)
        cv2.putText(img_exibicao, str(proxima_vaga), (x+10, y+10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        print(f"#vaga-{proxima_vaga} {{ top: {top}%; left: {left}%; }}")

img_original = cv2.imread(CAMINHO_IMAGEM)

if img_original is None:
    print("Erro ao carregar imagem")

else:

    escala = 0.5

    largura = int(img_original.shape[1] * escala)
    altura = int(img_original.shape[0] * escala)

    img_exibicao = cv2.resize(img_original, (largura, altura))

    cv2.namedWindow("Calibrador", cv2.WINDOW_NORMAL)
    cv2.imshow("Calibrador", img_exibicao)

    cv2.setMouseCallback("Calibrador", clique_mouse)

    print("Clique nas vagas. ESC para sair.")

    while True:

        cv2.imshow("Calibrador", img_exibicao)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cv2.destroyAllWindows()