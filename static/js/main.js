const socket = io();

const vagas = [
    { id: 1,  x: 27.96, y: 85.46 },
    { id: 2,  x: 28.88, y: 61.95, horizontal: true },
    { id: 3,  x: 28.88, y: 49.2,  horizontal: true },
    { id: 4,  x: 29.18, y: 41.04, horizontal: true },
    { id: 5,  x: 27.81, y: 13.55 },
    { id: 6,  x: 42.25, y: 12.95 },
    { id: 7,  x: 52.28, y: 12.95 },
    { id: 8,  x: 58.51, y: 12.95 },
    { id: 9,  x: 64.89, y: 13.15 },
    { id: 10, x: 71.43, y: 13.15 },
    { id: 11, x: 89.82, y: 11.75, horizontal: true },
    { id: 12, x: 90.27, y: 21.12, horizontal: true },
    { id: 13, x: 90.12, y: 30.48, horizontal: true },
    { id: 14, x: 89.97, y: 40.84, horizontal: true },
    { id: 15, x: 90.12, y: 49.2,  horizontal: true },
    { id: 16, x: 89.97, y: 61.75, horizontal: true },
    { id: 17, x: 90.12, y: 71.31, horizontal: true },
    { id: 18, x: 90.43, y: 78.88, horizontal: true },
    { id: 19, x: 90.73, y: 87.25, horizontal: true },
    { id: 20, x: 67.78, y: 78.09, horizontal: true },
    { id: 21, x: 68.09, y: 70.32, horizontal: true },
    { id: 22, x: 67.78, y: 61.55, horizontal: true },
    { id: 23, x: 67.63, y: 49.2,  horizontal: true },
    { id: 24, x: 67.63, y: 41.04, horizontal: true },
    { id: 25, x: 55.78, y: 41.04, horizontal: true },
    { id: 26, x: 56.23, y: 49.2,  horizontal: true },
    { id: 27, x: 56.38, y: 61.35, horizontal: true },
    { id: 28, x: 55.78, y: 70.72, horizontal: true },
    { id: 29, x: 56.08, y: 78.29, horizontal: true },
];

const vagasOcupadas = new Set();
const vagaCarrinho  = new Map();

const imgCarrinhos = [
    '/static/img/carrinho_ocupado.png',
].map(src => {
    const img = new Image();
    img.src = src;
    img.onload = desenharVagas;
    return img;
});

function desenharVagas() {
    const img    = document.getElementById('estacionamento');
    const canvas = document.getElementById('overlay');
    const rect   = img.getBoundingClientRect();

    canvas.width      = rect.width;
    canvas.height     = rect.height;
    canvas.style.left = img.offsetLeft + 'px';
    canvas.style.top  = img.offsetTop  + 'px';

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    vagas.forEach(v => {
        const cx = (v.x / 100) * rect.width;
        const cy = (v.y / 100) * rect.height;
        const w  = rect.width  * 0.055;
        const h  = rect.height * 0.10;
        const ocupada = vagasOcupadas.has(v.id);

        ctx.save();
        ctx.translate(cx, cy);
        if (v.horizontal) ctx.rotate(Math.PI / 2);

        ctx.strokeStyle = ocupada ? '#ff0000' : '#00ff00';
        ctx.fillStyle   = ocupada ? 'rgba(255,0,0,0.15)' : 'rgba(0,255,0,0.2)';
        ctx.lineWidth   = 2;
        ctx.beginPath();
        ctx.roundRect(-w/2, -h/2, w, h, 4);
        ctx.fill();
        ctx.stroke();

        if (ocupada) {
            const imgCarro = vagaCarrinho.get(v.id);
            if (imgCarro && imgCarro.complete) {
                ctx.drawImage(imgCarro, -w/2, -h/2, w, h);
            }
        }

        if (v.horizontal) ctx.rotate(-Math.PI / 2);
        ctx.fillStyle    = 'white';
        ctx.font         = `bold ${Math.max(9, w * 0.18)}px monospace`;
        ctx.textAlign    = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(v.id, 0, 0);

        ctx.restore();
    });

    if (typeof atualizarPainel === 'function') atualizarPainel();
}

document.getElementById('overlay').addEventListener('click', (e) => {
    const img  = document.getElementById('estacionamento');
    const rect = img.getBoundingClientRect();
    const mx   = e.offsetX;
    const my   = e.offsetY;

    vagas.forEach(v => {
        const cx = (v.x / 100) * rect.width;
        const cy = (v.y / 100) * rect.height;
        const w  = rect.width  * 0.07;
        const h  = rect.height * 0.13;

        if (mx >= cx - w/2 && mx <= cx + w/2 && my >= cy - h/2 && my <= cy + h/2) {
            if (vagasOcupadas.has(v.id)) {
                vagasOcupadas.delete(v.id);
                vagaCarrinho.delete(v.id);
                if (typeof registarEvento === 'function') registarEvento(v.id, 'livre');
            } else {
                vagasOcupadas.add(v.id);
                const sorteado = imgCarrinhos[Math.floor(Math.random() * imgCarrinhos.length)];
                vagaCarrinho.set(v.id, sorteado);
                if (typeof registarEvento === 'function') registarEvento(v.id, 'ocupada');
            }
            desenharVagas();
        }
    });
});

socket.on('update_vagas', (data) => {
    const count = document.getElementById('count');
    if (count) count.innerText = data.ocupadas;
    desenharVagas();
});

socket.on('evento_arduino', (data) => {
    if (typeof registarEvento === 'function') registarEvento('cancela', 'arduino');
});

window.addEventListener('resize', desenharVagas);
document.getElementById('estacionamento').addEventListener('load', desenharVagas);
desenharVagas();