import os
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import base64
from PIL import Image
import base64
import os

def get_base64_image():
    for ext in ["webp", "jpg", "jpeg", "png"]:
        image_path = f"back.{ext}"
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    return None

bg_img = get_base64_image()

# --- Page Setup ---
if bg_img:
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.35), rgba(255, 255, 255, 0)),
                        url("data:image/png;base64,{bg_img}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .block-container {{
            background-color: rgba(255, 248, 243, 0.45);
            padding: 2rem 3rem;
            border-radius: 18px;
            margin-top: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #c04600;
            font-family: 'Segoe UI', sans-serif;
        }}
        .export-buttons {{
            margin-top: 20px;
        }}
        .sidebar .sidebar-content {{
            background-color: #c04600;
            color: #f0e0d7;
        }}
        .sidebar .sidebar-content label, .sidebar .sidebar-content input, .sidebar .sidebar-content textarea, .sidebar .sidebar-content select {{
            color: #f0e0d7 !important;
        }}
        .sidebar .sidebar-content .stNumberInput > div > input,
        .sidebar .sidebar-content .stTextInput > div > input,
        .sidebar .sidebar-content .stTextArea > div > textarea {{
            background-color: #d15410;
            color: #f0e0d7 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# Configure the Gemini API key
genai.configure(api_key="AIzaSyASZINhUQHKEe4EE_w94ZsniPe_jCNVV1k")

# Text-to-speech function using gTTS
def speak(text):
    """Convert text to speech using gTTS and play it in the browser"""
    tts = gTTS(text=text, lang='en', slow=False)
    audio_bytes = BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    
    # Encode audio bytes to base64
    audio_base64 = base64.b64encode(audio_bytes.read()).decode('utf-8')
    audio_html = f"""
    <audio autoplay>
    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
    </audio>
    """
    st.components.v1.html(audio_html, height=0)

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file

def main():
    st.title("Medical Diagnosis Assistant")
    st.markdown("""
    <style>
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #c04600;
    }

    /* Sidebar text */
    [data-testid="stSidebar"] * {
        color: #f0e0d7 !important;
    }

    /* Input fields inside sidebar */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] select {
        background-color: #d15410 !important;
        color: #f0e0d7 !important;
        border-color: #f0e0d7;
    }

    /* Main heading color */
    h1, h2, h3, h4, h5, h6 {
        color: #c04600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    
    # Initialize session state
    if "info_submitted" not in st.session_state:
        st.session_state.info_submitted = False
    if "gemini_response" not in st.session_state:
        st.session_state.gemini_response = None
    
    # Sidebar for patient information
    with st.sidebar:
        st.header("Patient Information")
        
        # Personal Information
        age = st.number_input("Age", min_value=0, max_value=120, value=30)
        gender = st.radio("Gender", ["Male", "Female", "Other"])
        skin_type = st.selectbox(
            "Skin Type",
            ["Dry", "Oily", "Combination", "Sensitive", "Normal"]
        )
        
        # Medical Information
        severity = st.select_slider(
            "Condition Severity",
            options=["Mild", "Moderate", "Severe"]
        )
        problem = st.text_area("Describe your symptoms or condition")
        allergies = st.text_input("List any allergies")
        
        # Submit button
        if st.button("Submit Information", type="primary"):
            st.session_state.patient_info = {
                "age": age,
                "gender": gender,
                "skin_type": skin_type,
                "severity": severity,
                "problem": problem,
                "allergies": allergies
            }
            st.session_state.info_submitted = True
            st.success("Information submitted successfully!")
            speak("Thank you for providing your information. Please upload any medical images or documents for analysis.")
    
    # Main content area - only show after submission
    if st.session_state.get('info_submitted', False):
        st.header("Upload Medical Files")
        
        # File upload section
        uploaded_file = st.file_uploader(
            "Choose an image or document",
            type=["jpg", "jpeg", "png", "pdf"],
            help="Upload clear photos of affected area or medical reports"
        )
        
        if uploaded_file:
            # Display uploaded image if it's an image file
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Save the uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Determine MIME type
            mime_type = uploaded_file.type
            
            # Configure Gemini model
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config=generation_config,
            )
            
            # Create the prompt
            prompt = f"""
            Patient Information:
            - Age: {st.session_state.patient_info['age']}
            - Gender: {st.session_state.patient_info['gender']}
            - Skin Type: {st.session_state.patient_info['skin_type']}
            - Condition Severity: {st.session_state.patient_info['severity']}
            - Problem Description: {st.session_state.patient_info['problem']}
            - Allergies: {st.session_state.patient_info['allergies']}
            
            Please analyze the uploaded file along with the patient information and provide:
            1. Potential diagnosis
            2. Recommended next steps
            3. Treatment options
            4. When to seek immediate medical attention
            5. Prevention advice
            
            Provide your response in clear, patient-friendly language.
            it should be in  bullet points each should consist of 2 bullet points each points should be of 10 to 15 words
            """
            
            # Show loading spinner while processing
            with st.spinner("Analyzing your medical information..."):
                try:
                    # Upload file to Gemini
                    gemini_file = upload_to_gemini(temp_path, mime_type=mime_type)
                    
                    # Get response from Gemini
                    if mime_type.startswith('image'):
                        response = model.generate_content([prompt, gemini_file])
                    else:
                        response = model.generate_content([prompt, "File contents:", gemini_file])
                    
                    # Store and display response
                    st.session_state.gemini_response = response.text
                    
                    # Display results
                    st.header("Medical Assessment")
                    st.markdown(response.text)
                    
                    # Speak the beginning of the response
                    shortened_response = ' '.join(response.text.split()[:50]) + "..."
                    speak(f"Here is your medical assessment. {shortened_response}")
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    speak("Sorry, there was an error processing your request.")
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

if __name__ == "__main__":
    main()
