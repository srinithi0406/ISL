import streamlit as st
import os
from test import video_to_isl, save_isl_video

st.set_page_config(
    page_title="Speech to ISL Translator",
    page_icon="🤟",
    layout="centered"
)

st.title("🤟 Speech to Indian Sign Language Translator")
st.write("Upload a video with English speech and get ISL translation.")

# Create temp directory
os.makedirs("temp", exist_ok=True)

uploaded_video = st.file_uploader(
    "Upload English Speech Video",
    type=["mp4", "mov", "avi"]
)

if uploaded_video:
    input_path = os.path.join("temp", uploaded_video.name)

    with open(input_path, "wb") as f:
        f.write(uploaded_video.read())

    st.video(input_path)

    if st.button("Translate to ISL 🚀"):
        with st.spinner("Processing video → text → ISL..."):
            isl_sentences = video_to_isl(input_path)
            output_path = "temp/isl_translation.mp4"
            save_isl_video(isl_sentences, output_path)

        st.success("ISL Translation Complete ✅")

        st.video(output_path)

        with open(output_path, "rb") as f:
            st.download_button(
                label="Download ISL Video",
                data=f,
                file_name="isl_translation.mp4",
                mime="video/mp4"
            )