import streamlit as st
from fpdf import FPDF
import base64

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
    return st.session_state.slides[st.session_state.current_slide_idx]

def generate_image_from_prompt(prompt, width=1280, height=720):
    """
    *** PLACEHOLDER IMAGE GENERATION ***
    Generates a placeholder image URL.
    Replace this function with your actual image generation API call (e.g., to DALL-E, Midjourney, Imagen).
    The function should return the URL or bytes of the generated image.
    """
    # Using placeholder.com to simulate image generation with the correct aspect ratio
    encoded_prompt = base64.urlsafe_b64encode(prompt.encode()).decode()
    # Placeholder service can't take long URLs, so we shorten it.
    # The important part is that we have the full prompt available to us.
    display_text = "16:9 Image for Prompt"
    placeholder_url = f"https://via.placeholder.com/{width}x{height}/1E293B/FFFFFF.png?text={display_text}"
    return placeholder_url

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

    if st.button("⬇️ Move Slide Down", use_container_width=True, disabled=(idx == len(st.session_state.slides) - 1)):
        st.session_state.slides.insert(idx + 1, st.session_state.slides.pop(idx))
        st.session_state.current_slide_idx = idx + 1
        st.rerun()
    
    st.write("---")

    # Display slide thumbnails and handle selection
    for i, slide in enumerate(st.session_state.slides):
        with st.container(border=True):
            if i == st.session_state.current_slide_idx:
                st.subheader(f"Slide {i+1} (Selected)")
            else:
                st.write(f"Slide {i+1}")

            if st.button(f"Select Slide {i+1}", key=f"select_{slide['id']}", use_container_width=True):
                st.session_state.current_slide_idx = i
                st.rerun()
            
            if st.button(f"🗑️ Delete Slide {i+1}", key=f"delete_{slide['id']}", use_container_width=True):
                # Prevent deleting the last slide
                if len(st.session_state.slides) > 1:
                    st.session_state.slides.pop(i)
                    # Adjust current index if needed
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
        
        # Input variables as requested in the brief
        subject = st.text_input("Subject", "a silver dragon perched on a jagged cliff")
        action = st.text_input("Action", "roaring toward the stormy sky")
        environment = st.text_input("Environment", "craggy seaside coast at dusk")
        style = st.selectbox("Style", 
            ("digital matte painting, hyper-realistic", "illustration", "abstract", "photorealistic", "cel-shaded anime"), 
            help="Suggests relevant descriptions for the style variable.")
        perspective = st.text_input("Perspective", "low-angle shot")
        lighting = st.text_input("Lighting", "dramatic backlight with lightning flashes")
        color_palette = st.text_input("Color Palette", "dark slate grays with electric blue highlights")
        key_details = st.text_input("Key Details", "swirling mist around wings, ancient carved runes on cliff face")
        atmosphere = st.text_input("Atmosphere", "tense and awe-inspiring")
        composition = st.text_input("Composition", "dragon silhouette centered against lightning bolts")
        
        submitted = st.form_submit_button("Generate Image", use_container_width=True)

    if submitted:
        # Construct the final prompt by joining all filled variables
        final_prompt = (
            f"Subject: {subject}, Action: {action}, Environment: {environment}, Style: {style}, "
            f"Perspective: {perspective}, Lighting: {lighting}, Color Palette: {color_palette}, "
            f"Key Details: {key_details}, Atmosphere: {atmosphere}, Composition: {composition}. "
            f"Output Specs: 16:9 aspect ratio, 3840x2160"
        ).strip()
        
        with st.spinner("Generating image..."):
            # Store the prompt and generated image URL in a temporary state
            st.session_state.generated_prompt = final_prompt
            # This is the placeholder function call
            st.session_state.generated_image_url = generate_image_from_prompt(final_prompt)
    
    # Display the generated image and the 'Add to Slide' button
    if "generated_image_url" in st.session_state and st.session_state.generated_image_url:
        st.write("---")
        st.subheader("Generated Image")
        st.image(st.session_state.generated_image_url, caption="Generated Placeholder Image (16:9)")
        
        with st.expander("View Full Prompt"):
            st.write(st.session_state.generated_prompt)

        if st.button("✅ Add Image to Current Slide", use_container_width=True):
            slide = get_current_slide()
            slide['image_url'] = st.session_state.generated_image_url
            slide['image_prompt'] = st.session_state.generated_prompt
            # Clear the temporary state after adding
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
                pdf.ln(10)
                
                if slide.get('image_url'):
                    # We can't download external URLs directly into fpdf, so we add a link instead
                    # For a real implementation, you'd download the image bytes first
                    pdf.set_font("Arial", "", 12)
                    pdf.multi_cell(0, 10, f"Image included on slide (see app for visual). \nPrompt: {slide['image_prompt']}")
                    pdf.ln(5)
                
                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, slide['text'])

            # Create a download link for the generated PDF
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.markdown(create_download_link(pdf_output, "presentation.pdf"), unsafe_allow_html=True)
