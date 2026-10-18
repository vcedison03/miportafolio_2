import streamlit as st
import random
import re
import requests
import time
import difflib
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

# Configuración de la página y diseño con la gama de azules del portafolio (#2c3e50 y #34495e)
st.set_page_config(page_title="Test Interactivo de Inglés", page_icon="🎓", layout="centered")

# Estilos CSS personalizados para alinear la estética con la paleta de azules institucional
st.markdown("""
<style>
    /* Estilos generales inspirados en la paleta de azules */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Encabezado principal tipo header de portafolio */
    .main-header {
        background: #2c3e50;
        color: white;
        padding: 30px 20px;
        text-align: center;
        border-radius: 8px;
        margin-bottom: 25px;
    }
    .main-header h1 {
        color: white;
        font-size: 2.2rem;
        margin-bottom: 5px;
    }
    .main-header p {
        color: #ecf0f1;
        font-size: 1.1rem;
        opacity: 0.9;
    }

    /* Tarjetas de configuración y contenedores */
    .config-container {
        background: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #34495e;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
</style>

<div class="main-header">
    <h1>🎓 Test Interactivo de Inglés</h1>
    <p>Práctica de comprensión auditiva y traducción con fragmentos de libros clásicos</p>
</div>
""", unsafe_allow_html=True)

# Mensaje informativo
st.info("💡 **Recuerda:** Observa al final de la prueba la retrospectiva y tus audios guardados.")

# Inicializar estado de la sesión de Streamlit
if 'iniciado' not in st.session_state:
    st.session_state.iniciado = False
if 'oraciones' not in st.session_state:
    st.session_state.oraciones = []
if 'idx' not in st.session_state:
    st.session_state.idx = 0
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'aciertos' not in st.session_state:
    st.session_state.aciertos = 0
if 'suma_porcentajes' not in st.session_state:
    st.session_state.suma_porcentajes = 0.0
if 'titulo_libro' not in st.session_state:
    st.session_state.titulo_libro = ""
if 'respondido' not in st.session_state:
    st.session_state.respondido = False
if 'ultimo_resultado' not in st.session_state:
    st.session_state.ultimo_resultado = None
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False

# Controles de configuración en la página principal con el engranaje solicitado
st.markdown("---")
st.subheader("⚙️ Configuración del Test")

with st.container():
    nivel = st.selectbox("Nivel de exigencia:", ["Estricto (90%)", "Medio (75%)", "Flexible (60%)"])
    if "Estricto" in nivel:
        umbral_exito = 90.0
    elif "Flexible" in nivel:
        umbral_exito = 60.0
    else:
        umbral_exito = 75.0

    categoria = st.selectbox("Categoría de libros:", [
        "Physics & Electromagnetism", 
        "Astronomy & Space", 
        "Technology & Computing", 
        "Philosophy & Logic", 
        "Tema personalizado"
    ])

    temas_dict = {
        'Physics & Electromagnetism': 'physics',
        'Astronomy & Space': 'astronomy',
        'Technology & Computing': 'technology',
        'Philosophy & Logic': 'philosophy'
    }

    if categoria == "Tema personalizado":
        tema = st.text_input("Escribe tu tema en inglés:", "science")
    else:
        tema = temas_dict[categoria]

    st.markdown("---")
    st.subheader("📏 Longitud de oraciones")
    min_palabras = st.number_input("Cantidad mínima de palabras:", min_value=1, max_value=500, value=6, step=1)
    max_palabras = st.number_input("Cantidad máxima de palabras:", min_value=min_palabras, max_value=500, value=12, step=1)

    st.markdown("---")
    modo_cantidad = st.radio("Modo de cantidad de preguntas:", ["Número específico", "Indefinido (hasta salir)"])
    if modo_cantidad == "Número específico":
        cantidad_oraciones = st.number_input("¿Cuántas oraciones deseas responder?", min_value=1, max_value=500, value=5, step=1)
    else:
        cantidad_oraciones = "Indefinido"

st.markdown("---")

if not st.session_state.iniciado:
    if st.button("🚀 Cargar libro y comenzar test", type="primary"):
        with st.spinner(f"Buscando libros sobre '{tema}'..."):
            try:
                res = requests.get(f"https://gutendex.com/books/?search={tema}&languages=en", timeout=40).json()
                libros = res.get('results', [])
                if not libros:
                    st.error("No se encontraron libros para este tema.")
                else:
                    libro = random.choice(libros)
                    st.session_state.titulo_libro = libro.get('title', 'Desconocido')
                    text_url = libro.get('formats', {}).get('text/plain; charset=us-ascii') or libro.get('formats', {}).get('text/plain; charset=utf-8')
                    
                    if text_url:
                        text_url = text_url.replace("http://", "https://")
                        raw_text = requests.get(text_url, timeout=30).text
                        text_clean = re.sub(r"\s+", " ", raw_text)
                        
                        oraciones_filtradas = [
                            o.strip()
                            for o in re.split(r'(?<=[.!?])\s+', text_clean)
                            if min_palabras <= len(o.split()) <= max_palabras
                        ]
                        
                        if oraciones_filtradas:
                            random.shuffle(oraciones_filtradas)
                            
                            if cantidad_oraciones == "Indefinido":
                                st.session_state.oraciones = oraciones_filtradas
                            else:
                                st.session_state.oraciones = oraciones_filtradas[:int(cantidad_oraciones)]
                            
                            st.session_state.iniciado = True
                            st.session_state.idx = 0
                            st.session_state.historial = []
                            st.session_state.aciertos = 0
                            st.session_state.suma_porcentajes = 0.0
                            st.session_state.respondido = False
                            st.session_state.mostrar_resultados = False
                            st.rerun()
                        else:
                            st.warning(f"No se hallaron oraciones entre {min_palabras} y {max_palabras} palabras en este libro. Prueba cambiando los rangos o de tema.")
                    else:
                        st.error("El libro seleccionado no tiene formato de texto disponible.")
            except Exception as e:
                st.error(f"Error de red al conectar con Gutendex: {e}")

else:
    # Botón en la página principal para terminar en cualquier momento
    if not st.session_state.mostrar_resultados:
        if st.button("🛑 Terminar test y ver historial"):
            st.session_state.mostrar_resultados = True
            st.rerun()

    # Si se cumplieron las preguntas o se presionó salir
    if st.session_state.mostrar_resultados or st.session_state.idx >= len(st.session_state.oraciones):
        st.balloons()
        st.success("🎉 ¡Revisión finalizada con éxito!")
        st.markdown("---")
        st.subheader("="*10 + " RESULTADOS FINALES Y REVISIÓN " + "="*10)
        st.write(f"📚 **Libro:** {st.session_state.titulo_libro}")
        st.write(f"⚙️ **Nivel:** {nivel}")
        
        total_respuestas = len(st.session_state.historial)
        promedio = st.session_state.suma_porcentajes / total_respuestas if total_respuestas > 0 else 0
        
        st.metric("📝 Preguntas respondidas", total_respuestas)
        st.metric("✅ Aprobadas", f"{st.session_state.aciertos} de {total_respuestas}")
        st.metric("📊 Precisión promedio", f"{promedio:.1f}%")
        
        st.markdown("---")
        st.subheader("📋 LISTADO DE ORACIONES PRACTICADAS (RETROSPECTIVA):")
        
        if not st.session_state.historial:
            st.info("No hay oraciones registradas en el historial todavía.")
        else:
            for item in st.session_state.historial:
                with st.expander(f"Oración #{item['n']} ({item['calificacion']:.1f}% - {item['estado_str']})"):
                    st.write(f"**Original (EN):** {item['oracion']}")
                    st.write(f"**Tu respuesta:** {item['respuesta']}")
                    st.write(f"**Calificación:** {item['calificacion']:.1f}%")
                    if os.path.exists(item['audio']):
                        st.audio(item['audio'])
                        
        st.markdown("---")
        if st.button("🔄 Volver a empezar"):
            st.session_state.iniciado = False
            st.session_state.respondido = False
            st.session_state.mostrar_resultados = False
            st.rerun()
            
    else:
        # Pregunta en curso
        oracion_actual = st.session_state.oraciones[st.session_state.idx]
        
        st.subheader(f"📖 Libro: {st.session_state.titulo_libro}")
        
        if cantidad_oraciones == "Indefinido":
            st.markdown(f"**Pregunta #{st.session_state.idx + 1} (Modo Indefinido - Haz clic en 'Terminar test' arriba cuando desees parar)**")
        else:
            st.markdown(f"**Pregunta #{st.session_state.idx + 1} de {len(st.session_state.oraciones)}**")
        
        # Generar audio
        nombre_audio = f"temp_audio_{st.session_state.idx}.mp3"
        try:
            tts = gTTS(text=oracion_actual, lang='en')
            tts.save(nombre_audio)
            st.audio(nombre_audio, format='audio/mp3')
        except Exception:
            st.warning("No se pudo generar el audio automáticamente.")

        st.info("🎧 Escucha el audio anterior y escribe abajo lo que entendiste o traduce la oración.")
        
        if not st.session_state.respondido:
            with st.form(key=f"form_q_{st.session_state.idx}"):
                modo_traduccion = st.selectbox("¿Cómo deseas responder?", ['Traducir al Español (es)', 'Escribir en Inglés (en)'])
                respuesta_usuario = st.text_input("Tu respuesta:")
                enviar = st.form_submit_button("Calificar respuesta", type="primary")
                
                if enviar:
                    if not respuesta_usuario.strip():
                        st.warning("Por favor escribe una respuesta antes de calificar.")
                    else:
                        traductor = GoogleTranslator(source='en', target='es')
                        es_espanol = 'Español' in modo_traduccion
                        
                        esperada = ""
                        significado_es = ""
                        try:
                            if es_espanol:
                                esperada = traductor.translate(oracion_actual)
                            else:
                                significado_es = traductor.translate(oracion_actual)
                        except Exception:
                            esperada = oracion_actual
                            significado_es = oracion_actual
                            
                        if es_espanol:
                            similitud = difflib.SequenceMatcher(None, esperada.lower(), respuesta_usuario.lower()).ratio() * 100
                        else:
                            similitud = difflib.SequenceMatcher(None, oracion_actual.lower(), respuesta_usuario.lower()).ratio() * 100
                            
                        aprobado = similitud >= umbral_exito
                        estado_str = "¡Aprobado! ✅" if aprobado else "Por debajo del nivel ❌"
                        
                        if aprobado:
                            st.session_state.aciertos += 1
                            
                        st.session_state.total = st.session_state.idx + 1
                        st.session_state.suma_porcentajes += similitud
                        
                        st.session_state.historial.append({
                            'n': st.session_state.idx + 1,
                            'oracion': oracion_actual,
                            'respuesta': respuesta_usuario,
                            'calificacion': similitud,
                            'estado_str': estado_str,
                            'audio': nombre_audio
                        })
                        
                        st.session_state.ultimo_resultado = {
                            'similitud': similitud,
                            'estado_str': estado_str,
                            'es_espanol': es_espanol,
                            'esperada': esperada,
                            'significado_es': significado_es,
                            'respuesta': respuesta_usuario
                        }
                        st.session_state.respondido = True
                        st.rerun()
        else:
            res_u = st.session_state.ultimo_resultado
            st.success(f"Calificación: {res_u['similitud']:.1f}% -> {res_u['estado_str']}")
            st.write(f"✍️ **Tu respuesta:** {res_u['respuesta']}")
            if res_u['es_espanol']:
                st.write(f"🎯 **Traducción esperada:** {res_u['esperada']}")
            else:
                st.write(f"📖 **Significado en español:** {res_u['significado_es']}")
            st.markdown("---")
            if st.button("Siguiente oración ➡️", type="primary"):
                st.session_state.idx += 1
                st.session_state.respondido = False
                st.rerun()
