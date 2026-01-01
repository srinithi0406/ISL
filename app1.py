import streamlit as st
import os
import time
from test import video_to_isl, audio_to_isl, text_to_isl, save_isl_video


st.set_page_config(
    page_title="VISTA| English to ISL",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Main background and font */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Header styling */
    .main-title {
        font-size: 3rem !important;
        font-weight: 800 !important;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        font-size: 1.2rem !important;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Card-like container for inputs */
    .stSecondaryBlock {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #1E3A8A;
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #3B82F6;
        border: none;
        color: white;
        transform: translateY(-2px);
    }

    /* Success message styling */
    .stSuccess {
        background-color: #ecfdf5;
        color: #065f46;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)


os.makedirs("temp", exist_ok=True)


st.markdown('<h1 class="main-title"> VISTA</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Bridging the gap with Indian Sign Language (ISL) Translation</p>', unsafe_allow_html=True)


col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader(" Input Source")
    with st.container(border=True):
        input_type = st.segmented_control(
            "Select Translation Mode",
            ["Video", "Audio", "Text"],
            default="Text"
        )
        
        st.divider()

        uploaded_file = None
        text_input = ""

        if input_type == "Video":
            uploaded_file = st.file_uploader("Upload Speech Video", type=["mp4", "mov", "avi"])
            if uploaded_file:
                st.info(f"File uploaded: {uploaded_file.name}")

        elif input_type == "Audio":
            uploaded_file = st.file_uploader("Upload Speech Audio", type=["wav", "mp3", "m4a"])
            if uploaded_file:
                st.audio(uploaded_file)

        else:
            text_input = st.text_area(
                "Type your message...",
                placeholder="Example: How are you?",
                height=150
            )

        process_btn = st.button("Generate ISL Translation")

with col2:
    st.subheader(" ISL Output")
    
    if (uploaded_file is not None or (input_type == "Text" and text_input.strip())):
        if process_btn:
            
            input_path = None
            if input_type != "Text":
                input_path = os.path.join("temp", uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.read())

           
            with st.status("Converting to Indian Sign Language...", expanded=True) as status:
                st.write("Analyzing input...")
                
                if input_type == "Video":
                    isl_sentences = video_to_isl(input_path)
                elif input_type == "Audio":
                    isl_sentences = audio_to_isl(input_path)
                else:
                    isl_sentences = text_to_isl(text_input)
                
                if isl_sentences:
                    st.write("Synthesizing ISL Video...")
                    output_path = "temp/isl_translation.mp4"
                    save_isl_video(isl_sentences, output_path)
                    status.update(label="Translation Complete!", state="complete", expanded=False)
                else:
                    status.update(label="Translation Failed", state="error")
                    st.error("Could not process the input.")

            
            if os.path.exists("temp/isl_translation.mp4"):
                st.video("temp/isl_translation.mp4")
                
                with open("temp/isl_translation.mp4", "rb") as f:
                    st.download_button(
                        label=" Download ISL Translation",
                        data=f,
                        file_name="isl_translation.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
    else:
        
        st.info("Translation will appear here once you upload/type and click 'Generate'.")
        



# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #9CA3AF;'>Powered by Team VISTA ©️ 2025</div>", 
    unsafe_allow_html=True
)