# 🤟 Speech to Indian Sign Language (ISL) Translator

A Streamlit-based web application that translates English speech from uploaded videos into Indian Sign Language (ISL) using a grammar-aware NLP pipeline and pre-recorded ISL sign videos.

This project goes beyond word-by-word translation by understanding sentence structure and reordering grammar to match **ISL syntax (Subject-Object-Verb)**.

---

## 🚀 Features
* **🎥 Video Upload:** Support for `.mp4`, `.mov`, and `.avi` formats.
* **🔊 Automatic Transcription:** Uses **OpenAI Whisper** for high-accuracy speech-to-text.
* **🧠 ISL Grammar Engine:** Uses **spaCy** to transform English syntax into ISL-compliant grammar.
* **🤟 Hybrid Rendering:** Uses word-level sign videos; falls back to letter-by-letter finger-spelling if a word is missing.
* **🎬 Video Synthesis:** Automatically stitches sign clips into a seamless output video.
* **⬇️ Export:** Download the final ISL translation for offline use.

---


## 🎥 Demo & Sample Outputs

### ▶️ Full Demo Video
Watch the end-to-end working of the system here:  
🔗 https://youtu.be/E-bwoYySqlQ

---

### 📥 Input Video1 (English Speech)
This is the original input video containing spoken English used for translation.  
🔗 [View Input Video1](assets/sample5.mp4)


### 📤 Output Video1 (ISL Translation)
This is the generated Indian Sign Language (ISL) video output after grammar-aware processing.  
🔗 [View Output Video1](assets/isl_translation.mp4)

---

### 📥 Input Video2 (English Speech)
This is the original input video containing spoken English used for translation.  
🔗 [View Input Video2](assets/sample4.mp4)


### 📤 Output Video2 (ISL Translation)
This is the generated Indian Sign Language (ISL) video output after grammar-aware processing.  
🔗 [View Output Video2](assets/isl_translation%20(5).mp4)

---


## 🧠 How It Works (Pipeline)



1.  **Audio Extraction:** MoviePy extracts audio from the uploaded video.
2.  **Speech-to-Text:** Whisper converts the audio into raw English text.
3.  **NLP Processing:** spaCy parses the text to identify parts of speech (POS).
4.  **Grammar Mapping:** The system reorders the text (e.g., "What is your name?" becomes "Your name what?").
5.  **Video Stitching:** The backend searches the `assets/` folder for matching `.mp4` clips and merges them.

---

## 🧩 System Architecture (High-Level)
```text
English Speech Video
↓
Audio Extraction
↓
Speech-to-Text (Whisper)
↓
NLP Parsing (spaCy)
↓
ISL Grammar Reordering (SOV)
↓
Asset Mapping (Word / Alphabet)
↓
Video Stitching (MoviePy)
↓
Final ISL Output Video
```
---


## 🗂️ Project Structure
```text
ISL/
│
├── assets/                  # ISL sign videos (words + alphabets)
│   ├── hello.mp4
│   ├── time.mp4
│   ├── A.mp4
│   └── ...
│
├── temp/                    # Directory for processed files
│
├── app.py                   # Streamlit frontend UI
├── main.py                  # Backend (NLP & Video Logic)
│
├── requirements.txt         # Python dependencies
├── packages.txt             # OS-level dependencies (FFmpeg)
├── runtime.txt              # Python version
└── README.md
```

## 🛠️ Tech Stack

- **Frontend:** Streamlit  
- **Speech AI:** OpenAI Whisper  
- **NLP:** spaCy  
- **Video Engine:** MoviePy & OpenCV  
- **System:** FFmpeg (for video encoding)


## 📦 Installation & Setup

Follow these steps to get the project running on your local machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/](https://github.com/)<srinithi0406/>/ISL.git
cd ISL
```
**2. Set Up a Virtual Environment**
It is highly recommended to use a virtual environment to avoid dependency conflicts.

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```
**macOS / Linux:**

```bash

python -m venv venv
source venv/bin/activate
```
**3. Install Python Dependencies**
Install the required libraries and download the spaCy NLP model.
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```
**4. Install FFmpeg**
FFmpeg is required for video and audio processing. The app will not work without it.
**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```
**Windows:**
1. Download the "essentials" build from gyan.dev.
2. Extract the folder and add the bin directory to your System PATH.

▶️**Running the Application**
Once the setup is complete, launch the Streamlit interface:

```bash

streamlit run app.py
```
The application will automatically open in your browser at http://localhost:8501.

---

**🤟ISL Asset Handling Logic**
If a word-level ISL video exists, it is used directly
If not, the system finger-spells the word letter-by-letter
Asset naming format:
```text

hello.mp4
time.mp4
A.mp4
B.mp4
```
---
**🔮 Future Enhancements**
Avatar-based ISL generation (3D / pose estimation)
Support for non-manual grammar markers
Real-time speech-to-ISL translation
Expanded ISL vocabulary coverage
Mobile and low-bandwidth optimization

---
**📜 License**

This project is intended for educational and research purposes.
ISL video assets should be used responsibly and with proper permissions.

---

**🤝 Acknowledgements**

Built with the goal of improving accessibility and inclusive communication
for the Indian Deaf community 🇮🇳
