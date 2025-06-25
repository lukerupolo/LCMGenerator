import streamlit as st
from fpdf import FPDF
import base64
import requests # Needed to download the image for PDF export
from openai import OpenAI # Import the OpenAI library

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Art Director's Briefing Tool",
    page_icon="🎨",
    layout="wide"
)

# --- STATE MANAGEMENT ---
if 'slides' not in st.session_state:
    st.session_state.slides = [{
        'id': 0,
        'title': 'Slide 1: Title',
        'text': 'Add your bullet points here.',
        'image_prompt': None,
        'image_url': None,
        'image_bytes': None # Store image bytes for PDF export
    }]
if 'current_slide_idx' not in st.session_state:
    st.session_state.current_slide_idx = 0
if 'next_id' not in st.session_state:
    st.session_state.next_id = 1

# --- HELPER FUNCTIONS ---

def get_current_slide():
    """Returns the dictionary for the currently selected slide."""
    return st.session_state.slides[st.session_state.current_slide_idx]

def generate_image_from_prompt(prompt):
    """
    *** REAL IMAGE GENERATION - Updated Function ***
    Generates an image using the OpenAI DALL-E 3 API.
    It securely accesses the API key from st.secrets.
    """
    try:
        # 1. Access the secret API key from Streamlit's secrets manager
        api_key = st.secrets["OPENAI_API_KEY"]
        if not api_key:
            st.error("OpenAI API key is not set in secrets. Please add it.")
            return None, None

        # 2. Instantiate the OpenAI client
        client = OpenAI(api_key=api_key)

        # 3. Make the API call to DALL-E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",  # 16:9 aspect ratio for DALL-E 3
            quality="standard",
            n=1,
        )

        # 4. Get the URL of the generated image
        image_url = response.data[0].url
        
        # 5. Download the image bytes to store for PDF export
        image_response = requests.get(image_url)
        image_response.raise_for_status() # Raise an exception for bad status codes
        image_bytes = image_response.content

        return image_url, image_bytes

    except Exception as e:
        # If the key is not found or the API call fails, show an error.
        st.error(f"An error occurred during image generation: {e}")
        return None, None


def create_download_link(val, filename):
    """Creates a download link for a file."""
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}">Download PDF</a>'

# --- UI LAYOUT ---
col_left, col_center, col_right = st.columns([0.2, 0.5, 0.3])

# --- LEFT SIDEBAR (Slide Management) ---
with col_left:
    st.header("Slides")
    st.write("---")

    if st.button("➕ Add New Slide", use_container_width=True):
        new_slide = {
            'id': st.session_state.next_id,
            'title': f'Slide {st.session_state.next_id + 1}: New Slide',
            'text': '',
            'image_prompt': None,
            'image_url': None,
            'image_bytes': None
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

    if st.button("⬇️ Move Slide Down", use_container_width=True, disabled=(idx == len(st.session_state.slides) - 1)):
        st.session_state.slides.insert(idx + 1, st.session_state.slides.pop(idx))
        st.session_state.current_slide_idx = idx + 1
        st.rerun()
    
    st.write("---")

    for i, slide in enumerate(st.session_state.slides):
        with st.container(border=True):
            is_selected = (i == st.session_state.current_slide_idx)
            label = f"**Slide {i+1} (Selected)**" if is_selected else f"Slide {i+1}"
            st.markdown(label)
            
            if not is_selected and st.button(f"Select", key=f"select_{slide['id']}", use_container_width=True):
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
        key_details = st.text_input("Key Details", "swirling mist around wings")
        atmosphere = st.text_input("Atmosphere", "tense and awe-inspiring")
        composition = st.text_input("Composition", "dragon silhouette centered against lightning")
        submitted = st.form_submit_button("Generate Image", use_container_width=True, type="primary")

    if submitted:
        final_prompt = (f"Subject: {subject}, Action: {action}, Environment: {environment}, Style: {style}, "
                        f"Perspective: {perspective}, Lighting: {lighting}, Color Palette: {color_palette}, "
                        f"Key Details: {key_details}, Atmosphere: {atmosphere}, Composition: {composition}.")
        with st.spinner("Generating image... This may take a moment."):
            image_url, image_bytes = generate_image_from_prompt(final_prompt)
            if image_url and image_bytes:
                st.session_state.generated_prompt = final_prompt
                st.session_state.generated_image_url = image_url
                st.session_state.generated_image_bytes = image_bytes

    if "generated_image_url" in st.session_state and st.session_state.generated_image_url:
        st.write("---")
        st.subheader("Generated Image")
        st.image(st.session_state.generated_image_url, caption="Generated from API")
        if st.button("✅ Add Image to Current Slide", use_container_width=True):
            slide = get_current_slide()
            slide['image_url'] = st.session_state.generated_image_url
            slide['image_bytes'] = st.session_state.generated_image_bytes
            slide['image_prompt'] = st.session_state.generated_prompt
            del st.session_state.generated_image_url
            del st.session_state.generated_image_bytes
            del st.session_state.generated_prompt
            st.rerun()

    # --- EXPORT SECTION ---
    st.write("---")
    st.header("Export Presentation")
    if st.button("Export to PDF", use_container_width=True):
        with st.spinner("Creating PDF..."):
            pdf = FPDF()
            for i, slide in enumerate(st.session_state.slides):
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, slide['title'], 0, 1, 'C')
                pdf.ln(5)
                
                if slide.get('image_bytes'):
                    # Embed the image directly into the PDF from memory
                    pdf.image(BytesIO(slide['image_bytes']), x=10, y=30, w=190)
                    pdf.ln(110) # Adjust space after image

                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, slide['text'])

            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.markdown(create_download_link(pdf_output, "presentation.pdf"), unsafe_allow_html=True)

