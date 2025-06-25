import streamlit as st
from fpdf import FPDF
import base64
from openai import OpenAI
import requests # Needed to download the image for PDF embedding
import httpx

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Art Director's Briefing Tool",
    page_icon="🎨",
    layout="wide"
)

# --- STATE MANAGEMENT ---
# Initialize session state to hold the presentation slides and current selection
if 'slides' not in st.session_state:
    # Each slide is a dictionary
    st.session_state.slides = [{
        'id': 0,
        'title': 'Slide 1: Title',
        'text': 'Add your bullet points here.',
        'image_prompt': None,
        'image_url': None
    }]
if 'current_slide_idx' not in st.session_state:
    st.session_state.current_slide_idx = 0
if 'next_id' not in st.session_state:
    st.session_state.next_id = 1

# --- HELPER FUNCTIONS ---

def get_current_slide():
    """Returns the dictionary for the currently selected slide."""
    if not st.session_state.slides:
        # Handle case where all slides are deleted
        st.session_state.slides = [{
            'id': 0, 'title': 'Slide 1', 'text': '', 'image_prompt': None, 'image_url': None
        }]
        st.session_state.current_slide_idx = 0
        st.session_state.next_id = 1
    return st.session_state.slides[st.session_state.current_slide_idx]

# app.py

def generate_image_from_prompt(prompt):
    """
    Generates an image using the OpenAI DALL-E 3 API.
    It securely reads the API key and explicitly configures the HTTP client
    to avoid proxy-related errors.
    """
    try:
        # 1. Securely access the API key from Streamlit secrets
        api_key = st.secrets["OPENAI_API_KEY"]
        if not api_key:
            st.error("OpenAI API key is not set in Streamlit secrets.")
            return None

        # 2. Explicitly create an httpx client, bypassing environment proxies <--- NEW
        http_client = httpx.Client(proxies={})

        # 3. Initialize the OpenAI client with the key AND our new http_client <--- UPDATED
        client = OpenAI(api_key=api_key, http_client=http_client)

        # 4. Make the API call to generate the image
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )

        # 5. Extract the URL of the generated image
        image_url = response.data[0].url
        return image_url

    except Exception as e:
        # Handle cases where the secret is missing or the API call fails
        st.error(f"Failed to generate image. Error: {e}")
        return None

def create_download_link(val, filename):
    """Creates a download link for a file."""
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}">Download PDF</a>'

# --- UI LAYOUT ---
# Define the three main columns for the layout
col_left, col_center, col_right = st.columns([0.2, 0.5, 0.3])

# --- LEFT SIDEBAR (Slide Management) ---
with col_left:
    st.header("Slides")
    st.write("---")

    # Add and Reorder Buttons
    if st.button("➕ Add New Slide", use_container_width=True):
        new_slide = {
            'id': st.session_state.next_id,
            'title': f'Slide {st.session_state.next_id + 1}: New Slide',
            'text': '',
            'image_prompt': None,
            'image_url': None
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

    # Display slide thumbnails and handle selection
    for i, slide in enumerate(st.session_state.slides):
        with st.container(border=True):
            is_selected = (i == st.session_state.current_slide_idx)
            label = f"Slide {i+1}" + (" (Selected)" if is_selected else "")
            
            if st.button(label, key=f"select_{slide['id']}", use_container_width=True, type="primary" if is_selected else "secondary"):
                st.session_state.current_slide_idx = i
                st.rerun()
            
            if st.button(f"🗑️ Delete", key=f"delete_{slide['id']}", use_container_width=True):
                if len(st.session_state.slides) > 1:
                    st.session_state.slides.pop(i)
                    if st.session_state.current_slide_idx >= i:
                        st.session_state.current_slide_idx = max(0, st.session_state.current_slide_idx - 1)
                    st.rerun()
                else:
                    st.warning("Cannot delete the last slide.")

# --- CENTER PANEL (Slide Editor) ---
with col_center:
    st.header("Presentation Editor")
    st.write("---")
    
    current_slide = get_current_slide()

    # Edit Title
    new_title = st.text_input("Slide Title", value=current_slide['title'], key=f"title_{current_slide['id']}")
    current_slide['title'] = new_title

    # Edit Text
    new_text = st.text_area("Slide Text / Bullet Points", value=current_slide['text'], height=200, key=f"text_{current_slide['id']}")
    current_slide['text'] = new_text

    st.write("---")
    st.subheader("Slide Preview")

    # Display the image on the slide if it exists
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
        style = st.selectbox("Style", ("digital matte painting, hyper-realistic", "illustration", "abstract", "photorealistic", "cel-shaded anime"), help="Suggests relevant descriptions for the style variable.")
        perspective = st.text_input("Perspective", "low-angle shot")
        lighting = st.text_input("Lighting", "dramatic backlight with lightning flashes")
        color_palette = st.text_input("Color Palette", "dark slate grays with electric blue highlights")
        key_details = st.text_input("Key Details", "swirling mist around wings, ancient carved runes on cliff face")
        atmosphere = st.text_input("Atmosphere", "tense and awe-inspiring")
        composition = st.text_input("Composition", "dragon silhouette centered against lightning bolts")
        
        submitted = st.form_submit_button("Generate Image", use_container_width=True, type="primary")

    if submitted:
        final_prompt = (
            f"Subject: {subject}, Action: {action}, Environment: {environment}, Style: {style}, "
            f"Perspective: {perspective}, Lighting: {lighting}, Color Palette: {color_palette}, "
            f"Key Details: {key_details}, Atmosphere: {atmosphere}, Composition: {composition}. "
            f"Output Specs: 16:9 aspect ratio, 3840x2160"
        ).strip()
        
        with st.spinner("Contacting the digital artist (DALL-E 3)... Please wait."):
            image_url = generate_image_from_prompt(final_prompt)
            if image_url:
                st.session_state.generated_prompt = final_prompt
                st.session_state.generated_image_url = image_url
            else:
                # Error is already shown by the helper function
                pass
    
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
                        # Download image data from URL
                        response = requests.get(slide['image_url'])
                        response.raise_for_status() # Raise an exception for bad status codes
                        # Save image to a temporary file
                        with open("temp_image.jpg", "wb") as f:
                            f.write(response.content)
                        # Add image to PDF - calculate position to center it
                        pdf.image("temp_image.jpg", x=10, y=30, w=pdf.w - 20)
                        pdf.ln(105) # Adjust space after image
                    except requests.exceptions.RequestException as e:
                        pdf.set_font("Arial", "I", 10)
                        pdf.multi_cell(0, 5, f"(Could not download image for PDF: {e})")

                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, slide['text'])

            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.markdown(create_download_link(pdf_output, "presentation.pdf"), unsafe_allow_html=True)
