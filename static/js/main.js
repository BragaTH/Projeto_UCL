const socket = io();

const vagas = [
    { id: 1,  x: 42.25, y: 12.95 },
    { id: 2,  x: 52.28, y: 12.95 },
    { id: 3,  x: 58.51, y: 12.95 },
    { id: 4,  x: 64.89, y: 13.15 },
    { id: 5,  x: 71.43, y: 13.15 },
    { id: 6,  x: 89.82, y: 11.75, horizontal: true },
    { id: 7,  x: 90.27, y: 21.12, horizontal: true },
    { id: 8,  x: 90.12, y: 30.48, horizontal: true },
    { id: 9,  x: 89.97, y: 40.84, horizontal: true },
    { id: 10, x: 90.12, y: 49.2,  horizontal: true },
    { id: 11, x: 89.97, y: 61.75, horizontal: true },
    { id: 12, x: 90.12, y: 71.31, horizontal: true },
    { id: 13, x: 90.43, y: 78.88, horizontal: true },
    { id: 14, x: 90.73, y: 87.25, horizontal: true },
    { id: 15, x: 67.78, y: 78.09, horizontal: true },
    { id: 16, x: 68.09, y: 70.32, horizontal: true },
    { id: 17, x: 67.78, y: 61.55, horizontal: true },
    { id: 18, x: 67.63, y: 49.2,  horizontal: true },
    { id: 19, x: 67.63, y: 41.04, horizontal: true },
    { id: 20, x: 55.78, y: 41.04, horizontal: true },
    { id: 21, x: 56.23, y: 49.2,  horizontal: true },
    { id: 22, x: 56.38, y: 61.35, horizontal: true },
    { id: 23, x: 55.78, y: 70.72, horizontal: true },
    { id: 24, x: 56.08, y: 78.29, horizontal: true },
];

const vagasOcupadas = new Set();
const vagaCarrinho  = new Map();

const LS_INTERDITADAS = 'smartpark_interditadas';
const LS_TEMPO_EST = 'tempo_estabilidade';
const LS_ESTABILIDADE_LEGACY = 'smartpark_estabilidade_seg';

function carregarInterditadas() {
    try {
        const arr = JSON.parse(localStorage.getItem(LS_INTERDITADAS) || '[]');
        return new Set(
            arr
                .map((x) => parseInt(x, 10))
                .filter((n) => !Number.isNaN(n) && n >= 1 && n <= 24)
        );
    } catch (e) {
        return new Set();
    }
}

function guardarInterditadas(set) {
    try {
        localStorage.setItem(LS_INTERDITADAS, JSON.stringify([...set].sort((a, b) => a - b)));
    } catch (e) {}
}

const vagasInterditadas = carregarInterditadas();
window.vagasInterditadas = vagasInterditadas;

window.totalVagasPainel = 24;

window.getEstabilidadeSegundos = function () {
    const raw =
        localStorage.getItem(LS_TEMPO_EST) ||
        localStorage.getItem(LS_ESTABILIDADE_LEGACY) ||
        '5';
    const v = parseInt(raw, 10);
    return [3, 5, 8, 10].includes(v) ? v : 5;
};

window.definirTempoEstabilidade = function (segundos) {
    const t = [3, 5, 8, 10].includes(Number(segundos)) ? Number(segundos) : 5;
    try {
        localStorage.setItem(LS_TEMPO_EST, String(t));
    } catch (e) {}
    if (socket.connected) {
        socket.emit('set_tempo_estabilidade', { tempo: t });
    }
};

socket.on('connect', function () {
    const t = window.getEstabilidadeSegundos();
    try {
        localStorage.setItem(LS_TEMPO_EST, String(t));
    } catch (e) {}
    socket.emit('set_tempo_estabilidade', { tempo: t });
});

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
        const interditada = vagasInterditadas.has(v.id);
        const ocupada = !interditada && vagasOcupadas.has(v.id);

        ctx.save();
        ctx.translate(cx, cy);
        if (v.horizontal) ctx.rotate(Math.PI / 2);

        if (interditada) {
            ctx.strokeStyle = '#ffc800';
            ctx.fillStyle = 'rgba(255, 200, 0, 0.4)';
            ctx.lineWidth = 3;
        } else {
            ctx.strokeStyle = ocupada ? '#ff0000' : '#00ff00';
            ctx.fillStyle = ocupada ? 'rgba(255,0,0,0.15)' : 'rgba(0,255,0,0.2)';
            ctx.lineWidth = 2;
        }
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
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        if (interditada) {
            ctx.font = `${Math.max(12, w * 0.22)}px "Segoe UI Emoji", "Apple Color Emoji", sans-serif`;
            ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
            ctx.fillText('\uD83D\uDEA7', 0, -h * 0.14);
        }
        ctx.fillStyle = 'white';
        ctx.font = `bold ${Math.max(9, w * 0.18)}px monospace`;
        ctx.fillText(v.id, 0, interditada ? h * 0.1 : 0);

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
            if (vagasInterditadas.has(v.id)) {
                vagasInterditadas.delete(v.id);
            } else {
                vagasInterditadas.add(v.id);
                vagasOcupadas.delete(v.id);
                vagaCarrinho.delete(v.id);
            }
            guardarInterditadas(vagasInterditadas);
            desenharVagas();
        }
    });
});

socket.on('update_vagas', (data) => {
    const count = document.getElementById('count');
    if (count) count.innerText = data.ocupadas;

    if (typeof data.total === 'number' && data.total > 0) {
        window.totalVagasPainel = data.total;
    }

    vagasOcupadas.clear();
    vagaCarrinho.clear();
    if (Array.isArray(data.vagas_ocupadas)) {
        const imgCar = imgCarrinhos[0];
        data.vagas_ocupadas.forEach((id) => {
            const n = typeof id === 'number' ? id : parseInt(id, 10);
            if (!Number.isNaN(n) && n >= 1 && !vagasInterditadas.has(n)) {
                vagasOcupadas.add(n);
                if (imgCar) vagaCarrinho.set(n, imgCar);
            }
        });
    }

    desenharVagas();
});

socket.on('evento_arduino', (data) => {
    if (typeof registarEvento === 'function') registarEvento('cancela', 'arduino');
});

socket.on('contador_carros', (data) => {
    const total = Number(data && data.total);
    const valor = Number.isFinite(total) && total >= 0 ? String(total) : '0';
    const elPainel = document.getElementById('total-carros-num');
    const elTopo = document.getElementById('total-carros-topo-num');
    if (elPainel) elPainel.textContent = valor;
    if (elTopo) elTopo.textContent = valor;
});

const gridMapa = document.getElementById('mapa-vagas-grid');
if (gridMapa) {
    gridMapa.addEventListener('click', (e) => {
        const cell = e.target.closest('.mv');
        if (!cell || !cell.id) return;
        const id = parseInt(cell.id.replace('mv-', ''), 10);
        if (Number.isNaN(id) || id < 1) return;
        if (vagasInterditadas.has(id)) {
            vagasInterditadas.delete(id);
        } else {
            vagasInterditadas.add(id);
            vagasOcupadas.delete(id);
            vagaCarrinho.delete(id);
        }
        guardarInterditadas(vagasInterditadas);
        desenharVagas();
    });
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const m = document.getElementById('modal-config');
        if (m && m.classList.contains('modal-config--aberto') && typeof fecharConfig === 'function') {
            fecharConfig();
        }
    }
});

window.addEventListener('resize', desenharVagas);
document.getElementById('estacionamento').addEventListener('load', desenharVagas);
desenharVagas();