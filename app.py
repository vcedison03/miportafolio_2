import streamlit as st

import random
import re
import requests
import time
import difflib
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

st.set_page_config(page_title="Test Interactivo de Inglés", page_icon="🎓", layout="centered")

st.title("🎓 Práctica de Inglés: Test Interactivo con Libros")
st.write("Practica tu comprensión auditiva y traducción con fragmentos de libros clásicos.")

# Mensaje solicitado en la pantalla principal
st.info("💡 **Recuerda:** Observa al final de la prueba la retrospectiva y tus audios guardados.")

# Configuración inicial en la página principal (en lugar de barra lateral)
st.markdown("---")
st.header("⚙️ Configuración")

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

# Filtros de longitud de palabras con números abiertos y tan grandes como quieras
st.markdown("---")
st.subheader("📏 Longitud de oraciones")
min_palabras = st.number_input("Cantidad mínima de palabras:", min_value=1, max_value=500, value=6, step=1)
max_palabras = st.number_input("Cantidad máxima de palabras:", min_value=min_palabras, max_value=500, value=12, step=1)

# Selección de cantidad: Número específico o Indefinido
st.markdown("---")
modo_cantidad = st.radio("Modo de cantidad de preguntas:", ["Número específico", "Indefinido (hasta salir)"])
if modo_cantidad == "Número específico":
    cantidad_oraciones = st.number_input("¿Cuántas oraciones deseas responder?", min_value=1, max_value=500, value=5, step=1)
else:
    cantidad_oraciones = "Indefinido"

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
            st.session_state.mostrar_resultados
