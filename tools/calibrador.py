import cv2

CAMINHO_IMAGEM = '../static/img/estacionamento.png'
CONTAINER_W = 659
CONTAINER_H = 502

vagas_coordenadas = []

def calcular_imagem_renderizada(img_w, img_h, cont_w, cont_h):
    ratio_img = img_w / img_h
    ratio_cont = cont_w / cont_h
    if ratio_img > ratio_cont:
        render_w = cont_w
        render_h = int(cont_w / ratio_img)
    else:
        render_h = cont_h
        render_w = int(cont_h * ratio_img)
    offset_x = (cont_w - render_w) // 2
    offset_y = (cont_h - render_h) // 2
    return render_w, render_h, offset_x, offset_y

def clique_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        render_w, render_h, offset_x, offset_y = calcular_imagem_renderizada(
            img_original.shape[1], img_original.shape[0], CONTAINER_W, CONTAINER_H
        )
        x_rel = x - offset_x
        y_rel = y - offset_y
        if x_rel < 0 or y_rel < 0 or x_rel > render_w or y_rel > render_h:
            print("Clique fora da imagem, ignore.")
            return
        left = round((x_rel / render_w) * 100, 2)
        top  = round((y_rel / render_h) * 100, 2)
        vagas_coordenadas.append((top, left))
        proxima_vaga = len(vagas_coordenadas)
        cv2.circle(img_exibicao, (x, y), 5, (0, 255, 0), -1)
        cv2.putText(img_exibicao, str(proxima_vaga), (x + 10, y + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        print(f"  {{ id: {proxima_vaga}, x: {left}, y: {top} }},")

img_original = cv2.imread(CAMINHO_IMAGEM)

if img_original is None:
    print("Erro ao carregar imagem")
else:
    render_w, render_h, offset_x, offset_y = calcular_imagem_renderizada(
        img_original.shape[1], img_original.shape[0], CONTAINER_W, CONTAINER_H
    )
    img_exibicao = cv2.resize(img_original, (render_w, render_h))
    img_exibicao = cv2.copyMakeBorder(img_exibicao,
        offset_y, CONTAINER_H - render_h - offset_y,
        offset_x, CONTAINER_W - render_w - offset_x,
        cv2.BORDER_CONSTANT, value=(14, 17, 14))

    cv2.namedWindow("Calibrador", cv2.WINDOW_AUTOSIZE)
    cv2.imshow("Calibrador", img_exibicao)
    cv2.setMouseCallback("Calibrador", clique_mouse)

    print("Clique nas vagas. ESC para sair.")
    while True:
        cv2.imshow("Calibrador", img_exibicao)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    cv2.destroyAllWindows()