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
# This ensures the app state is preserved across reruns.
if 'slides' not in st.session_state:
    st.session_state.slides = [{'id': 0, 'title': 'Slide 1: Title', 'text': 'Add your bullet points here.', 'image_prompt': None, 'image_url': None}]
if 'current_slide_idx' not in st.session_state:
    st.session_state.current_slide_idx = 0
if 'next_id' not in st.session_state:
    st.session_state.next_id = 1

# --- HELPER FUNCTIONS ---

def get_current_slide():
    """
    Returns the dictionary for the currently selected slide.
    This function includes a safety check to prevent index errors if a slide
    is deleted, ensuring the app remains stable.
    """
    if 'slides' not in st.session_state or not st.session_state.slides:
        # If slides are empty for any reason, re-initialize to a default state.
        st.session_state.slides = [{'id': 0, 'title': 'Slide 1', 'text': '', 'image_prompt': None, 'image_url': None}]
        st.session_state.current_slide_idx = 0
        st.session_state.next_id = 1

    # Adjust the current index if it's out of bounds (e.g., after a deletion).
    if st.session_state.current_slide_idx >= len(st.session_state.slides):
        st.session_state.current_slide_idx = len(st.session_state.slides) - 1
    
    return st.session_state.slides[st.session_state.current_slide_idx]

def generate_image_from_prompt(prompt):
    """
    Generates an image using the OpenAI DALL-E 3 API.
    It securely reads the API key and explicitly configures an httpx.Client
    to avoid proxy-related errors, particularly in cloud deployment environments.
    """
    try:
        # Securely get the API key from Streamlit secrets.
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.error("OpenAI API key is not set. Please add it to your Streamlit secrets.")
            return None
        
        #
        # --- CRITICAL FIX FOR PROXY ERROR ---
        # The OpenAI library uses httpx for making API requests. In some environments
        # (like Streamlit Community Cloud), default system proxies can cause issues.
        # By initializing httpx.Client with empty proxies, we tell it to ignore
        # external proxy configurations, resolving the connection error.
        #
        http_client = httpx.Client(proxies={})

        # The OpenAI client is initialized with our custom http_client.
        # The 'proxies' argument is not passed to OpenAI directly, which was the cause of the error.
        client = OpenAI(api_key=api_key, http_client=http_client)

        # Make the API call to generate an image.
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024", # 16:9 aspect ratio for presentations
            quality="standard",
            n=1,
        )
        
        # Extract the URL of the generated image.
        image_url = response.data[0].url
        return image_url

    except Exception as e:
        # Display a detailed error message to help with debugging.
        st.error(f"Failed to generate image. Error: {e}")
        return None

def create_download_link(val, filename):
    """
    Creates a base64-encoded download link for a given file content.
    """
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}">Download PDF</a>'

# --- UI LAYOUT ---
# Create a three-column layout for the app interface.
col_left, col_center, col_right = st.columns([0.2, 0.5, 0.3])

# --- LEFT SIDEBAR (Slide Management) ---
with col_left:
    st.header("Slides")
    st.write("---")

    # Button to add a new slide to the presentation.
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
        st.rerun() # Rerun the app to reflect the changes immediately.

    idx = st.session_state.current_slide_idx
    # Buttons to reorder slides. They are disabled when the action is not possible.
    if st.button("⬆️ Move Slide Up", use_container_width=True, disabled=(idx == 0)):
        st.session_state.slides.insert(idx - 1, st.session_state.slides.pop(idx))
        st.session_state.current_slide_idx = idx - 1
        st.rerun()

    if st.button("⬇️ Move Slide Down", use_container_width=True, disabled=(idx >= len(st.session_state.slides) - 1)):
        st.session_state.slides.insert(idx + 1, st.session_state.slides.pop(idx))
        st.session_state.current_slide_idx = idx + 1
        st.rerun()
    
    st.write("---")

    # Display the list of slides, allowing selection and deletion.
    for i, slide in enumerate(list(st.session_state.slides)):
        with st.container(border=True):
            is_selected = (i == st.session_state.current_slide_idx)
            label = f"Slide {i+1}" + (" (Selected)" if is_selected else "")
            
            # Button to select a slide for editing.
            if st.button(label, key=f"select_{slide['id']}", use_container_width=True, type="primary" if is_selected else "secondary"):
                st.session_state.current_slide_idx = i
                st.rerun()
            
            # Button to delete a slide.
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
    
    # Input fields for editing the current slide's title and text.
    # Using a unique key linked to the slide ID ensures state is preserved correctly.
    new_title = st.text_input("Slide Title", value=current_slide['title'], key=f"title_{current_slide['id']}")
    current_slide['title'] = new_title
    new_text = st.text_area("Slide Text / Bullet Points", value=current_slide['text'], height=200, key=f"text_{current_slide['id']}")
    current_slide['text'] = new_text

    st.write("---")
    st.subheader("Slide Preview")

    # Display the image for the current slide if one has been added.
    if current_slide['image_url']:
        st.image(current_slide['image_url'], caption=f"Generated from: {current_slide['image_prompt']}")
    else:
        st.info("Generate an image in the right panel and add it to this slide.")

# --- RIGHT SIDEBAR (Image Generator) ---
with col_right:
    st.header("Image Generator")
    st.write("---")
    
    # A form to collect all the details needed to construct a detailed image prompt.
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
        # Construct the final, detailed prompt from the form inputs.
        final_prompt = (f"Subject: {subject}, Action: {action}, Environment: {environment}, Style: {style}, "
                        f"Perspective: {perspective}, Lighting: {lighting}, Color Palette: {color_palette}, "
                        f"Key Details: {key_details}, Atmosphere: {atmosphere}, Composition: {composition}. "
                        f"Output Specs: 16:9 aspect ratio, 3840x2160").strip()
        
        with st.spinner("Contacting the digital artist (DALL-E 3)... Please wait."):
            image_url = generate_image_from_prompt(final_prompt)
            if image_url:
                # Store the generated image and prompt in session state temporarily.
                st.session_state.generated_prompt = final_prompt
                st.session_state.generated_image_url = image_url
                st.rerun() # Rerun to display the new image outside the form block.

    # Display the newly generated image and provide an option to add it to the slide.
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
            # Clean up session state after adding the image.
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
                        # Download the image to a temporary file to embed it in the PDF.
                        response = requests.get(slide['image_url'])
                        response.raise_for_status() # Raise an exception for bad status codes
                        temp_image_path = f"temp_image_{i}.jpg"
                        with open(temp_image_path, "wb") as f:
                            f.write(response.content)
                        # Add image to PDF, calculating position.
                        pdf.image(temp_image_path, x=10, y=30, w=pdf.w - 20)
                        pdf.ln(105) # Add space to move text below the image.
                        os.remove(temp_image_path) # Clean up the temporary file.
                    except requests.exceptions.RequestException as e:
                        pdf.set_font("Arial", "I", 10)
                        pdf.multi_cell(0, 5, f"(Could not download image for PDF: {e})")

                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, slide['text'])

            # Generate the PDF content and create a download link.
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.markdown(create_download_link(pdf_output, "presentation.pdf"), unsafe_allow_html=True)
