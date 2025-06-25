import streamlit as st
from fpdf import FPDF
import base64
import httpx
from openai import OpenAI
import requests
import os

st.set_page_config(
    page_title="Art Director's Briefing Tool",
    page_icon="🎨",
    layout="wide"
)

if 'slides' not in st.session_state:
    st.session_state.slides = [{
        'id': 0,
        'title': 'Slide 1: Title',
        'text': 'Add your bullet points here.',
        'image_prompt': None,
        'image_url': None,
        'text_position': 'bottom'
    }]
if 'current_slide_idx' not in st.session_state:
    st.session_state.current_slide_idx = 0
if 'next_id' not in st.session_state:
    st.session_state.next_id = 1
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""

def generate_image_from_prompt(prompt: str, api_key: str) -> str | None:
    if not api_key:
        st.error("OpenAI API key is missing. Please enter it in the sidebar.")
        return None
    try:
        http_client = httpx.Client()
        client = OpenAI(api_key=api_key, http_client=http_client)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        msg = str(e)
        if "Incorrect API key" in msg:
            st.error("The provided OpenAI API key is incorrect. Please check and re-enter it.")
        else:
            st.error(f"Image generation failed: {msg}")
        return None

def create_pdf_bytes_from_slides(slides: list[dict]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for i, slide in enumerate(slides):
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, slide.get('title', ''), ln=1, align='C')
        pdf.ln(5)
        image_url = slide.get('image_url')
        if image_url:
            try:
                resp = requests.get(image_url)
                resp.raise_for_status()
                img_path = f"temp_slide_{i}.jpg"
                with open(img_path, 'wb') as f:
                    f.write(resp.content)
                pdf.image(img_path, x=10, y=30, w=pdf.w - 20)
                pdf.ln(105)
                os.remove(img_path)
            except Exception as img_err:
                pdf.set_font("Arial", "I", 10)
                pdf.multi_cell(0, 5, f"(Image embed failed: {img_err})")
                pdf.ln(5)
        position = slide.get('text_position', 'bottom')
        text = slide.get('text', '')
        pdf.set_fill_color(0, 0, 0)
        pdf.set_text_color(255, 255, 255)
        w = pdf.w - 20
        h = 50
        if position == 'top':
            x, y = 10, 30
        elif position == 'center':
            x, y = 10, (pdf.h / 2) - (h / 2)
        else:
            x, y = 10, pdf.h - h - 15
        pdf.rect(x, y, w, h, 'F')
        pdf.set_xy(x + 2, y + 2)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(w - 4, 8, text)
        pdf.set_text_color(0, 0, 0)
    pdf_data = pdf.output(dest='S')
    if isinstance(pdf_data, str):
        return pdf_data.encode('latin-1')
    return pdf_data

def create_download_link(val: bytes, filename: str) -> str:
    b64 = base64.b64encode(val).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download {filename}</a>'

col_left, col_center, col_right = st.columns([0.2, 0.5, 0.3])

with col_left:
    st.header("Settings")
    st.session_state.openai_api_key = st.text_input(
        "Enter OpenAI API Key",
        type="password",
        value=st.session_state.openai_api_key,
        help="Your API key is stored temporarily and not saved."
    )
    st.write("---")
    st.header("Slides")
    if st.button("➕ Add New Slide", use_container_width=True):
        new_slide = {
            'id': st.session_state.next_id,
            'title': f'Slide {st.session_state.next_id + 1}: New Slide',
            'text': '',
            'image_prompt': None,
            'image_url': None,
            'text_position': 'bottom'
        }
        st.session_state.slides.append(new_slide)
        st.session_state.next_id += 1
        st.session_state.current_slide_idx = len(st.session_state.slides) - 1
        st.rerun()
    idx = st.session_state.current_slide_idx
    if st.button("⬆️ Move Slide Up", use_container_width=True, disabled=(idx == 0)):
        st.session_state.slides.insert(idx - 1, st.session_state.slides.pop(idx))
        st.session_state.current_slide_idx = idx - 1
        st.rerun()
    if st.button("⬇️ Move Slide Down", use_container_width=True, disabled=(idx >= len(st.session_state.slides) - 1)):
        st.session_state.slides.insert(idx + 1, st.session_state.slides.pop(idx))
        st.session_state.current_slide_idx = idx + 1
        st.rerun()
    st.write("---")
    for i, slide in enumerate(list(st.session_state.slides)):
        with st.container(border=True):
            is_sel = (i == st.session_state.current_slide_idx)
            label = f"Slide {i+1}" + (" (Selected)" if is_sel else "")
            if st.button(label, key=f"select_{slide['id']}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state.current_slide_idx = i
                st.rerun()
            if st.button("🗑️ Delete", key=f"delete_{slide['id']}", use_container_width=True):
                if len(st.session_state.slides) > 1:
                    st.session_state.slides.pop(i)
                    st.rerun()
                else:
                    st.warning("Cannot delete the last slide.")

with col_center:
    st.header("Presentation Editor")
    st.write("---")
    curr = st.session_state.slides[st.session_state.current_slide_idx]
    title = st.text_input("Slide Title", value=curr['title'], key=f"title_{curr['id']}")
    curr['title'] = title
    text = st.text_area("Slide Text / Bullet Points", value=curr['text'], height=200, key=f"text_{curr['id']}")
    curr['text'] = text
    position = st.selectbox("Text Position", ['bottom', 'top', 'center'], index=['bottom', 'top', 'center'].index(curr.get('text_position', 'bottom')))
    curr['text_position'] = position
    st.write("---")
    st.subheader("Slide Preview")
    if curr.get('image_url'):
        st.image(curr['image_url'], caption=f"Generated from: {curr.get('image_prompt')}")
    else:
        st.info("Generate an image in the right panel and add it to this slide.")
    st.markdown(f"<div style='position:relative;width:100%;height:200px;'>"
                f"<div style='position:absolute;"
                f"bottom:{'0' if position=='bottom' else 'auto'};"
                f"top:{'0' if position=='top' else 'auto'};"
                f"left:0;right:0;"
                f"background-color:black;opacity:0.7;padding:10px;'>"
                f"<p style='color:white;margin:0;'>{text.replace('\n','<br>')}</p>"
                f"</div></div>", unsafe_allow_html=True)

with col_right:
    st.header("Image Generator")
    st.write("---")
    with st.form("prompt_form"):
        st.info("Fill out the variables below to construct the image prompt.")
        subject = st.text_input("Subject", "a silver dragon perched on a jagged cliff")
        action = st.text_input("Action", "roaring toward the stormy sky")
        environment = st.text_input("Environment", "craggy seaside coast at dusk")
        style = st.selectbox("Style", ("digital matte painting, hyper-realistic","illustration","abstract","photorealistic","cel-shaded anime"))
        perspective = st.text_input("Perspective", "low-angle shot")
        lighting = st.text_input("Lighting", "dramatic backlight with lightning flashes")
        color_palette = st.text_input("Color Palette", "dark slate grays with electric blue highlights")
        key_details = st.text_input("Key Details", "swirling mist around wings, ancient carved runes on cliff face")
        atmosphere = st.text_input("Atmosphere", "tense and awe-inspiring")
        composition = st.text_input("Composition", "dragon silhouette centered against lightning bolts")
        if st.form_submit_button("Generate Image", use_container_width=True, type="primary"):
            if not st.session_state.openai_api_key:
                st.error("Please enter your OpenAI API key in the left sidebar before generating an image.")
            else:
                final_prompt = (
                    f"Subject: {subject}, Action: {action}, Environment: {environment}, Style: {style}, "
                    f"Perspective: {perspective}, Lighting: {lighting}, Color Palette: {color_palette}, "
                    f"Key Details: {key_details}, Atmosphere: {atmosphere}, Composition: {composition}. "
                    f"Output Specs: 16:9 aspect ratio, 3840x2160"
                ).strip()
                with st.spinner("Contacting the digital artist (DALL-E 3)... Please wait."):
                    url = generate_image_from_prompt(final_prompt, st.session_state.openai_api_key)
                    if url:
                        st.session_state.generated_prompt = final_prompt
                        st.session_state.generated_image_url = url
                        st.rerun()
    if st.session_state.get("generated_image_url"):
        st.write("---")
        st.subheader("Generated Image")
        st.image(st.session_state.generated_image_url, caption="Generated by DALL-E 3")
        with st.expander("View Full Prompt"):
            st.write(st.session_state.generated_prompt)
        if st.button("✅ Add Image to Current Slide", use_container_width=True):
            slide = st.session_state.slides[st.session_state.current_slide_idx]
            slide['image_url'] = st.session_state.generated_image_url
            slide['image_prompt'] = st.session_state.generated_prompt
            del st.session_state.generated_image_url
            del st.session_state.generated_prompt
            st.rerun()

st.write("---")
st.header("Export Presentation")
if st.button("Export to PDF", use_container_width=True):
    with st.spinner("Creating PDF..."):
        pdf_bytes = create_pdf_bytes_from_slides(st.session_state.slides)
        st.markdown(create_download_link(pdf_bytes, "presentation.pdf"), unsafe_allow_html=True)
