import streamlit as st
from fpdf import FPDF
import base64
from openai import OpenAI
import requests
import httpx
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Art Director's Briefing Tool",
    page_icon="🎨",
    layout="wide"
)

# --- STATE MANAGEMENT ---
# Initialize session state variables if they don't exist.
if 'slides' not in st.session_state:
    st.session_state.slides = [{'id': 0, 'title': 'Slide 1: Title', 'text': 'Add your bullet points here.', 'image_prompt': None, 'image_url': None}]
if 'current_slide_idx' not in st.session_state:
    st.session_state.current_slide_idx = 0
if 'next_id' not in st.session_state:
    st.session_state.next_id = 1
# Add a new state variable to hold the user's API key
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""

# --- HELPER FUNCTIONS ---

def get_current_slide():
    """
    Returns the dictionary for the currently selected slide.
    Includes a safety check to prevent index errors after deletions.
    """
    if 'slides' not in st.session_state or not st.session_state.slides:
        st.session_state.slides = [{'id': 0, 'title': 'Slide 1', 'text': '', 'image_prompt': None, 'image_url': None}]
        st.session_state.current_slide_idx = 0
        st.session_state.next_id = 1

    if st.session_state.current_slide_idx >= len(st.session_state.slides):
        st.session_state.current_slide_idx = len(st.session_state.slides) - 1
    
    return st.session_state.slides[st.session_state.current_slide_idx]

def generate_image_from_prompt(prompt, api_key):
    """
    Generates an image using the OpenAI DALL-E 3 API with a user-provided key.
    Configures an httpx.Client to avoid proxy-related errors.
    """
    try:
        if not api_key:
            st.error("OpenAI API key is missing. Please enter it in the sidebar.")
            return None

        # Create an HTTPX client; proxies are handled at the HTTPX level, not in OpenAI init
        http_client = httpx.Client(proxies={})

        # Initialize the OpenAI client correctly with the custom HTTP client
        client = OpenAI(api_key=api_key, http_client=http_client)

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )

        # Extract and return the generated image URL
        image_url = response.data[0].url
        return image_url

    except Exception as e:
        error_msg = str(e)
        # Handle invalid API key error specifically
        if "Incorrect API key" in error_msg:
            st.error("The provided OpenAI API key is incorrect. Please check and re-enter it.")
        else:
            st.error(f"Failed to generate image. Error: {error_msg}")
        return None

def create_download_link(val, filename):
    """
    Creates a base64-encoded download link for a file.
    """
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}">Download PDF</a>'

# --- UI LAYOUT ---
col_left, col_center, col_right = st.columns([0.2, 0.5, 0.3])

# --- LEFT SIDEBAR (Slide Management) ---
with col_left:
    st.header("Settings")
    # Field for the user to input their OpenAI API key
    st.session_state.openai_api_key = st.text_input(
        "Enter OpenAI API Key", 
        type="password", 
        value=st.session_state.openai_api_key,
        help="Your API key is stored temporarily and not saved."
    )
    st.write("---")

    st.header("Slides")

    if st.button("➕ Add New Slide", use_container_width=True):
        new_slide = {'id': st.session_state.next_id, 'title': f'Slide {st.session_state.next_id + 1}: New Slide', 'text': '', 'image_prompt': None, 'image_url': None}
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
            is_selected = (i == st.session_state.current_slide_idx)
            label = f"Slide {i+1}" + (" (Selected)" if is_selected else "")
            
            if st.button(label, key=f"select_{slide['id']}", use_container_width=True, type="primary" if is_selected else "secondary"):
                st.session_state.current_slide_idx = i
                st.rerun()
            
            if st.button(f"🗑️ Delete", key=f"delete_{slide['id']}", use_container_width=True):
                if len(st.session_state.slides) > 1:
                    st.session_state.slides.pop(i)
                    st.rerun()
                else:
                    st.warning("Cannot delete the last slide.")

# --- CENTER PANEL (Slide Editor) ---
with col_center:
    st.header("Presentation Editor")
    st.write("---")
    
    current_slide = get_current_slide()
    
    new_title = st.text_input("Slide Title", value=current_slide['title'], key=f"title_{current_slide['id']}")
    current_slide['title'] = new_title
    new_text = st.text_area("Slide Text / Bullet Points", value=current_slide['text'], height=200, key=f"text_{current_slide['id']}")
    current_slide['text'] = new_text

    st.write("---")
    st.subheader("Slide Preview")

    if current_slide['image_url']:
        st.image(current_slide['image_url'], caption=f"Generated from: {current_slide['image_prompt']}")
    else:
        st.info("Generate an image in the right panel and add it to this slide.")

# --- RIGHT SIDEBAR (Image Generator) ---
with col_right:
    st.header("Image Generator")
    st.write("---")
    
    with st.form("prompt_form"):
        st.info("Fill out the variables below to construct the image prompt.")
        
        subject = st.text_input("Subject", "a silver dragon perched on a jagged cliff")
        action = st.text_input("Action", "roaring toward the stormy sky")
        environment = st.text_input("Environment", "craggy seaside coast at dusk")
        style = st.selectbox("Style", ("digital matte painting, hyper-realistic", "illustration", "abstract", "photorealistic", "cel-shaded anime"))
        perspective = st.text_input("Perspective", "low-angle shot")
        lighting = st.text_input("Lighting", "dramatic backlight with lightning flashes")
        color_palette = st.text_input("Color Palette", "dark slate grays with electric blue highlights")
        key_details = st.text_input("Key Details", "swirling mist around wings, ancient carved runes on cliff face")
        atmosphere = st.text_input("Atmosphere", "tense and awe-inspiring")
        composition = st.text_input("Composition", "dragon silhouette centered against lightning bolts")
        
        submitted = st.form_submit_button("Generate Image", use_container_width=True, type="primary")

    if submitted:
        if not st.session_state.openai_api_key:
            st.error("Please enter your OpenAI API key in the left sidebar before generating an image.")
        else:
            final_prompt = (f"Subject: {subject}, Action: {action}, Environment: {environment}, Style: {style}, "
                            f"Perspective: {perspective}, Lighting: {lighting}, Color Palette: {color_palette}, "
                            f"Key Details: {key_details}, Atmosphere: {atmosphere}, Composition: {composition}. "
                            f"Output Specs: 16:9 aspect ratio, 3840x2160").strip()
            
            with st.spinner("Contacting the digital artist (DALL-E 3)... Please wait."):
                # Pass the user's API key to the generation function
                image_url = generate_image_from_prompt(final_prompt, st.session_state.openai_api_key)
                if image_url:
                    st.session_state.generated_prompt = final_prompt
                    st.session_state.generated_image_url = image_url
                    st.rerun()

    if "generated_image_url" in st.session_state and st.session_state.generated_image_url:
        st.write("---")
        st.subheader("Generated Image")
        st.image(st.session_state.generated_image_url, caption="Generated by DALL-E 3")
        
        with st.expander("View Full Prompt"):
            st.write(st.session_state.generated_prompt)

        if st.button("✅ Add Image to Current Slide", use_container_width=True):
            slide = get_current_slide()
            slide['image_url'] = st.session_state.generated_image_url
            slide['image_prompt'] = st.session_state.generated_prompt
            del st.session_state.generated_image_url
            del st.session_state.generated_prompt
            st.rerun()

    # --- EXPORT SECTION ---
    st.write("---")
    st.header("Export Presentation")
    if st.button("Export to PDF", use_container_width=True):
        with st.spinner("Creating PDF..."):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            for i, slide in enumerate(st.session_state.slides):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, slide['title'], 0, 1, 'C')
                pdf.ln(5)
                
                if slide.get('image_url'):
                    try:
                        response = requests.get(slide['image_url'])
                        response.raise_for_status()
                        temp_image_path = f"temp_image_{i}.jpg"
                        with open(temp_image_path, "wb") as f:
                            f.write(response.content)
                        pdf.image(temp_image_path, x=10, y=30, w=pdf.w - 20)
                        pdf.ln(105)
                        os.remove(temp_image_path)
                    except requests.exceptions.RequestException as e:
                        pdf.set_font("Arial", "I", 10)
                        pdf.multi_cell(0, 5, f"(Could not download image for PDF: {e})")

                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, slide['text'])

            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.markdown(create_download_link(pdf_output, "presentation.pdf"), unsafe_allow_html=True)
