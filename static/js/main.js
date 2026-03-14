// conecta no socket do Flask
const socket = io();

// pega o carro animado
const carro = document.getElementById('carro-animado');


// CLIQUE MANUAL NAS VAGAS
document.querySelectorAll('.vaga').forEach(vaga => {

    vaga.addEventListener('click', () => {

        // alterna entre ocupada e livre
        vaga.classList.toggle('ocupada');

    });

});

// ATUALIZAÇÃO DAS VAGAS (YOLO)
socket.on('update_vagas', (data) => {

    const count = document.getElementById('count');

    if(count){
        count.innerText = data.ocupadas;
    }

    if(data.deteccoes.length > 0){

        carro.style.display = 'block';

        carro.style.left = data.deteccoes[0].x + '%';
        carro.style.top  = data.deteccoes[0].y + '%';

    }

});


// EVENTOS DO ARDUINO
socket.on('evento_arduino', (data) => {

    alert(data.msg);

});