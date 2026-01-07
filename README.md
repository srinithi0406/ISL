#  Speech to Indian Sign Language (ISL) Translator

A **Flask-based, real-time, grammar-aware Speech-to-Indian Sign Language (ISL) translation system** that converts **English speech, audio files, video files, and live microphone input** into ISL videos using NLP-driven grammar transformation and pre-recorded ISL sign assets.

This project goes beyond word-by-word translation by understanding **sentence structure** and converting English grammar into **ISL-compliant Subject–Object–Verb (SOV) order**, enabling more natural and meaningful ISL output..

---
## Key Features

### 1. Multi-Input Support
- **Text Input**
- **Audio File Upload** (`.wav`, `.mp3`)
- **Video File Upload** (`.mp4`, `.mov`, `.avi`)
- **Real-time Microphone Input (Live Speech)**

---

### 2. Intelligent Language Processing
- **Grammar-aware ISL translation**
- Sentence-level parsing using **spaCy**
- Clause detection, POS tagging, and ISL grammar reordering
- Handles negation, time expressions and modifiers

---

### 3. Speech-to-Text (Google-powered)
- **Google Web Speech API** for:
  - Audio file input
  - Extracted video audio
- **Google Streaming Speech-to-Text API** for:
  - Real-time microphone-based speech recognition
- Automatic punctuation enabled for better sentence segmentation

---

### 4. ISL Video Generation
- Word-level ISL sign videos (if available)
- Automatic **finger-spelling fallback** (letter-by-letter) if a word video is missing
- Seamless stitching of ISL sign clips using MoviePy
- Downloadable final ISL output video

---

### 5. Real-Time Translation Pipeline
- Live audio converted to text **incrementally**
- Sentence chunks pushed into a **Text Queue**
- ISL tokens generated and pushed into a **Video Queue**
- ISL sign videos streamed and displayed in sequence with minimal latency

---

### 6. Web-Based Interface
- **Flask backend**
- **Socket.IO (WebSockets)** for real-time updates:
  - Live transcript
  - ISL tokens
  - ISL video playback
- Responsive frontend (HTML/CSS/JS)

---



## Demo & Sample Outputs

### Full Demo Video
Watch the end-to-end working of the system here:  
🔗 https://youtu.be/E-bwoYySqlQ

---

### Input Video1 (English Speech)
This is the original input video containing spoken English used for translation.  
🔗 [View Input Video1](assets/sample5.mp4)


### Output Video1 (ISL Translation)
This is the generated Indian Sign Language (ISL) video output after grammar-aware processing.  
🔗 [View Output Video1](assets/isl_translation.mp4)

---

### Input Video2 (English Speech)
This is the original input video containing spoken English used for translation.  
🔗 [View Input Video2](assets/sample4.mp4)


### Output Video2 (ISL Translation)
This is the generated Indian Sign Language (ISL) video output after grammar-aware processing.  
🔗 [View Output Video2](assets/isl_translation%20(5).mp4)

---

## How It Works (Pipeline)

1. **Input Handling:** The system accepts text, audio files, video files, or live microphone input.
2. **Audio Extraction:** For video inputs, audio is extracted using MoviePy.
3. **Speech-to-Text:**  
   - Audio and video files are transcribed using the **Google Web Speech API**.  
   - Live microphone input is transcribed in real time using the **Google Streaming Speech-to-Text API**.
4. **Real-Time Text Queueing:** During live speech, transcribed text is incrementally pushed into a **text queue** as the user speaks.
5. **Sentence Segmentation:** The transcribed text is split into sentences for independent processing.
6. **NLP Processing:** spaCy performs POS tagging, dependency parsing, and clause analysis.
7. **ISL Grammar Mapping:** English sentences are reordered into **ISL-compliant Subject–Object–Verb (SOV)** structure.
8. **ISL Asset Mapping:** Each ISL token is mapped to a word-level sign video, with **finger-spelling fallback** when required.
9. **Rendering & Output:**  
   - For text/audio/video inputs, ISL sign clips are stitched into a final output video.  
   - For real-time input, ISL videos are queued and streamed continuously with **low latency**.


---

## System Architecture (High-Level)

```text
Input Sources
(Text / Audio / Video / Live Mic)
        ↓
Audio Extraction (Video only)
        ↓
Speech-to-Text
- Google Web Speech API (files)
- Google Streaming STT (real-time)
        ↓
Sentence Segmentation
        ↓
spaCy NLP Parsing
(POS tagging, dependency parsing)
        ↓
ISL Grammar Reordering (SOV)
        ↓
ISL Token Generation
        ↓
Asset Mapping
(Word video → fallback to finger-spelling)
        ↓
Video Queue (Real-time)
        ↓
ISL Video Rendering & Playback

```


## Project Structure
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

## Tech Stack

- **Frontend:** HTML/CSS/JS
- **Backend Framework:** Flask
- **Speech API:** Google Web Speech API, Google Streaming STT
- **NLP:** spaCy  
- **Video Engine:** MoviePy & OpenCV  
- **System:** FFmpeg (for video encoding)


## Installation & Setup

Follow these steps to get the project running on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com/srinithi0406/ISL.git
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

**Running the Application**
Once the setup is complete, launch the Streamlit interface:

```bash

python app.py
```
The application will automatically open in your browser.

---

**ISL Asset Handling Logic**
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
**Future Enhancements**
- Avatar-based ISL generation (3D / pose estimation)
- Support for non-manual grammar markers
- Expanded ISL vocabulary coverage
- Mobile and low-bandwidth optimization

---
**License**

This project is intended for educational and research purposes.
ISL video assets should be used responsibly and with proper permissions.

---

**🤝 Acknowledgements**

Built with the goal of improving accessibility and inclusive communication
for the Indian Hearing Impaired community 🇮🇳

