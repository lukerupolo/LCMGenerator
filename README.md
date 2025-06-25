# LCMGenerator
Generates Image art and Message of the day then exports to presentation slide
# Art Director's Briefing Tool

## High-Level Vision
A game franchise-specific visual art and message-of-the-day image generator for briefing agencies.

## Description
This Streamlit application allows users to create presentations by generating images from highly specific, structured prompts. It's designed to help art directors and creative teams build detailed visual briefs for agencies, ensuring clarity and consistency.

The app features a three-column layout:
- **Left Sidebar:** Manage presentation slides (add, delete, reorder, select).
- **Center Panel:** View and edit the selected slide (title, text, and image).
- **Right Sidebar:** The "Image Generator," where users fill out detailed variables to construct a prompt and generate an image.

**Note:** The image generation is currently simulated. The app constructs the complete, detailed prompt as specified and uses a placeholder service to return an image with the correct 16:9 aspect ratio. This allows for full testing of the UI and workflow. To connect to a real image model, replace the `generate_image_from_prompt` function in `app.py` with your chosen API call.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run the App

1.  **Navigate to the project directory in your terminal.**
2.  **Run the following command:**
    ```bash
    streamlit run app.py
    ```
3.  The application will open in a new tab in your web browser.
