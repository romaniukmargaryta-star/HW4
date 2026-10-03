import streamlit as st 
import os
import cv2
import numpy as np
import urllib.parse
import requests 
from PIL import Image
from io import BytesIO 
import io
from dotenv import load_dotenv

load_dotenv()

def generat_image(prompt):
    try: 
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"
        response = requests.get(url, timeout=45)
        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"ошібачка ({response.status_code}) "
    except requests.exceptions.Timeout:
        return None, f"сєрвєр недоступін"
    except Exception as e:
        return None, f"помилка при генерации зображення: {e}"

st.title("Генератор зображень з фільтрами")

if "current_img_array" not in st.session_state:
    st.session_state["current_img_array"] = None

st.subheader("1. General")
promt = st.text_area("Введіть опис зображення", placeholder="Наприклад: котик в космосі")

STYLES = {
    "Без стилю": "",
    "Реалістичний": "high detail, photorealistic, natural lighting",
    "Акварель": "watercolor painting style, soft edges, pastel colors",
    "Мультяшний": "3D animated movie style, vibrant colors, friendly look",
    "Піксель-Арт": "pixel art style, 16-bit retro game aesthetic"
}

style_choice = st.selectbox("Стиль ШІ", list(STYLES.keys()))

if st.button("Сгенерувати зображення через ШІ"):
    if promt.strip() == "":
        st.warning("Будь ласка, введіть текст промту!")
    else:
        full_prompt = f"{promt}, {STYLES[style_choice]}" if STYLES[style_choice] else promt
        
        with st.spinner("Генерація зображення... Зачекайте"):
            image_bytes, error = generat_image(full_prompt)
            
        if error:
            st.error(f"Не вдалося сгенерувати зображення: {error}")
        elif image_bytes:
            image = Image.open(BytesIO(image_bytes))
            st.session_state["current_img_array"] = np.array(image.convert("RGB"))
            st.success("Зображення успішно створено ШІ! Філітри доступні нижче.")

st.subheader("Або завантажте власне foto")
uploaded_file = st.file_uploader("Оберіть зображення...", type=["png", "jpeg", "jpg"])

if uploaded_file is not None: 
    image = Image.open(uploaded_file)
    st.session_state["current_img_array"] = np.array(image.convert("RGB"))

if st.session_state["current_img_array"] is not None:
    img_array = st.session_state["current_img_array"]
    
    st.sidebar.header("Налаштування фільтру")
    filter_option = st.sidebar.selectbox(
        "Виберіть ефект:", 
        ["оріг", "інверсія", "хорошое качество", "яркость", "чб"]
    )
    
    processed_img = img_array.copy()

    if filter_option == "чб": 
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        processed_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        
    elif filter_option == "хорошое качество":
        processed_img = cv2.GaussianBlur(img_array, (15, 15), 0)
        
    elif filter_option == "яркость":
        processed_img = cv2.convertScaleAbs(img_array, alpha=1.0, beta=50)
        
    elif filter_option == "інверсія": 
        processed_img = 255 - img_array

    col1, col2 = st.columns(2)
    
    with col1: 
        st.subheader("Оригінал")
        st.image(img_array, use_container_width=True)
        
    with col2:
        st.subheader("Після фільтру")
        st.image(processed_img, use_container_width=True)

        result_img = Image.fromarray(processed_img)
        buf = io.BytesIO()
        result_img.save(buf, format="JPEG")
        byte_im = buf.getvalue()

        st.download_button(
            label="💾 Завантажити оброблене фото", 
            data=byte_im,
            file_name="filtered_image.jpeg",
            mime="image/jpeg"
        )