// script.js - VERSIÓ MILLORADA
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const botonEntrar = document.getElementById('entrar-portal');
    const botonTornar = document.getElementById('tornar-inici');
    const paginaPrincipal = document.getElementById('pagina-principal');
    const paginaPortal = document.getElementById('pagina-portal');

    // STREAMS - URLs dinàmiques basades en la ubicació actual
    const streamReal = document.getElementById('stream-real');
    const streamVirtual = document.getElementById('stream-virtual');
    
    // Obtenir el domini actual i construir URLs relatives
    const baseUrl = window.location.origin.replace(/:\d+$/, ':8080');
    const STREAM_REAL_URL = `${baseUrl}/video_feed_real`;
    const STREAM_VIRTUAL_URL = `${baseUrl}/video_feed_virtual`;
    
    let streamsActius = false;

    // Funcio per a entrar al portal
    botonEntrar.addEventListener('click', function() {
        paginaPrincipal.classList.remove('pagina-activa');
        paginaPrincipal.classList.add('pagina-oculta');
        paginaPortal.classList.remove('pagina-oculta');
        paginaPortal.classList.add('pagina-activa');
        iniciarStreams();
    });
    
    // Función para volver al inicio
    botonTornar.addEventListener('click', function() {
        paginaPortal.classList.remove('pagina-activa');
        paginaPortal.classList.add('pagina-oculta');
        paginaPrincipal.classList.remove('pagina-oculta');
        paginaPrincipal.classList.add('pagina-activa');
        aturarStreams();
    });

    function iniciarStreams(){
        if(!streamsActius){
            console.log('Iniciant streams des de:', baseUrl);
            
            // Afegir timestamp per evitar cache
            const timestamp = new Date().getTime();
            streamReal.src = `${STREAM_REAL_URL}?t=${timestamp}`;
            streamVirtual.src = `${STREAM_VIRTUAL_URL}?t=${timestamp}`;

            // CORRECCIÓ: IDs correctes
            streamReal.classList.remove('error-stream');
            streamVirtual.classList.remove('error-stream');

            streamsActius = true;
        }
    }

    function aturarStreams() {
        streamReal.src = '';
        streamVirtual.src = '';
        streamsActius = false;
    }

    // Gestió d'errors millorada
    streamReal.addEventListener('error', function() {
        console.error('Error carregant stream real:', STREAM_REAL_URL);
        streamReal.classList.add('error-stream');
        // Reintentar després de 3 segons
        setTimeout(() => {
            if(streamsActius) {
                streamReal.src = `${STREAM_REAL_URL}?t=${new Date().getTime()}`;
            }
        }, 3000);
    });

    streamVirtual.addEventListener('error', function() {
        console.error('Error carregant stream virtual:', STREAM_VIRTUAL_URL);
        streamVirtual.classList.add('error-stream');
        // Reintentar després de 3 segons
        setTimeout(() => {
            if(streamsActius) {
                streamVirtual.src = `${STREAM_VIRTUAL_URL}?t=${new Date().getTime()}`;
            }
        }, 3000);
    });

    // Event per quan els streams es carreguen correctament
    streamReal.addEventListener('load', function() {
        streamReal.classList.remove('error-stream');
        console.log('Stream real carregat correctament');
    });

    streamVirtual.addEventListener('load', function() {
        streamVirtual.classList.remove('error-stream');
        console.log('Stream virtual carregat correctament');
    });
});