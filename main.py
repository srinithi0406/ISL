import spacy
import whisper
from moviepy import VideoFileClip, concatenate_videoclips
import os
import streamlit as st
import speech_recognition as sr
import re

# =====================================================
# 0. LOAD MODELS (CACHED FOR STREAMLIT)
# =====================================================

@st.cache_resource
def load_models():
    print("[INFO] Loading spaCy model: en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

    print("[INFO] Loading Whisper model: base")
    whisper_model = whisper.load_model("base")

    print("[INFO] Models loaded successfully")
    return nlp, whisper_model

nlp, whisper_model = load_models()

# =====================================================
# 1. GRAMMAR-BASED ISL PIPELINE
# =====================================================

def process_clause(tokens):
    time_tokens, object_tokens, subject_tokens = [], [], []
    verb_tokens, negation_tokens, modifiers = [], [], []

    for token in tokens:
        if token.ent_type_ in ("DATE", "TIME"):
            time_tokens.append(token.text.upper())
        elif token.pos_ in ("ADV", "ADP") and token.text.lower() in (
            "before", "after", "immediately", "now", "later"
        ):
            modifiers.append(token.text.upper())
        elif token.pos_ == "ADV":
            object_tokens.append(token.text.upper())
        elif token.dep_ in ("nsubj", "nsubjpass") and token.text.lower() != "it":
            subject_tokens.append(token.text.upper())
        elif token.pos_ == "VERB":
            verb_tokens.append(token.lemma_.upper())
        elif token.dep_ in ("dobj", "pobj", "attr", "acomp"):
            object_tokens.append(token.text.upper())
        elif token.dep_ == "neg":
            negation_tokens.append("NOT")

    isl_clause = (
        time_tokens + modifiers + object_tokens +
        subject_tokens + verb_tokens + negation_tokens
    )

    print("\n[DEBUG] Clause Processing")
    print(" Tokens:", [t.text for t in tokens])
    print(" ISL Clause:", isl_clause)
    print("-" * 60)

    return isl_clause


def split_clauses(doc):
    condition_tokens, main_tokens = set(), set(doc)

    for token in doc:
        if token.dep_ == "advcl":
            for sub in token.subtree:
                condition_tokens.add(sub)
                main_tokens.discard(sub)
        if token.text.lower() == "if":
            for sub in token.head.subtree:
                condition_tokens.add(sub)
                main_tokens.discard(sub)

    return list(condition_tokens), list(main_tokens)


def english_to_isl(sentence):
    print("\n[INPUT SENTENCE]", sentence)

    doc = nlp(sentence)
    condition_tokens, main_tokens = split_clauses(doc)

    condition_isl = process_clause(condition_tokens)
    main_isl = process_clause(main_tokens)

    final_isl = condition_isl + [","] + main_isl if condition_isl else main_isl
    print("[FINAL ISL TOKENS]", final_isl)

    return final_isl

# =====================================================
# 2. SPEECH TO TEXT (GOOGLE → WHISPER FALLBACK)
# =====================================================

def extract_audio_from_video(video_path, audio_path="temp_audio.wav"):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, logger=None)
    return audio_path


def google_speech_to_text(audio_path):
    print("\n[INFO] Running Google Web Speech API")
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
        print("[GOOGLE STT OUTPUT]", text)
        return text
    except Exception as e:
        print("[ERROR] Google STT failed:", e)
        return ""


def whisper_speech_to_text(audio_path):
    print("\n[INFO] Running Whisper fallback")
    result = whisper_model.transcribe(audio_path)
    print("[WHISPER OUTPUT]", result["text"])
    return result["text"]


def needs_fallback(text):
    if not text:
        return True
    if not re.search(r"[.!?]", text):
        print("[WARN] No punctuation detected")
        return True

    doc = nlp(text)
    if len(list(doc.sents)) == 1 and len(text.split()) > 12:
        print("[WARN] Single long sentence detected")
        return True

    return False


def speech_to_text(audio_path):
    text = google_speech_to_text(audio_path)

    if needs_fallback(text):
        print("[INFO] Falling back to Whisper")
        text = whisper_speech_to_text(audio_path)
    else:
        print("[INFO] Google STT accepted")

    return text

# =====================================================
# 3. VIDEO / AUDIO / TEXT → ISL
# =====================================================

def video_to_isl(video_path):
    print("\n[INFO] Processing video:", video_path)

    audio_path = extract_audio_from_video(video_path)
    text = speech_to_text(audio_path)

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    print("[INFO] Sentences detected:", sentences)

    return [english_to_isl(s) for s in sentences]


def audio_to_isl(audio_path):
    print("\n[INFO] Processing audio:", audio_path)

    text = speech_to_text(audio_path)

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    print("[INFO] Sentences detected:", sentences)

    return [english_to_isl(s) for s in sentences]


def text_to_isl(text):
    print("\n[INFO] Processing text input")
    print("[TEXT INPUT]", text)

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    print("[INFO] Sentences detected:", sentences)

    return [english_to_isl(s) for s in sentences]

# =====================================================
# 4. ISL TOKENS → VIDEO CLIPS
# =====================================================

ASSET_DIR = "./assets"
DISPLAY_TIME_WORD = 2.5
DISPLAY_TIME_LETTER = 0.8


def isl_tokens_to_clips(isl_tokens):
    clips = []
    for token in isl_tokens:
        token = token.lower()
        video_path = os.path.join(ASSET_DIR, f"{token}.mp4")

        if os.path.exists(video_path):
            clips.append(VideoFileClip(video_path).with_duration(DISPLAY_TIME_WORD))
        else:
            for ch in token:
                if ch.isalpha():
                    letter_path = os.path.join(ASSET_DIR, f"{ch.upper()}.mp4")
                    if os.path.exists(letter_path):
                        clips.append(
                            VideoFileClip(letter_path).with_duration(DISPLAY_TIME_LETTER)
                        )
    return clips

# =====================================================
# 5. SAVE FINAL VIDEO
# =====================================================

def save_isl_video(all_isl_sentences, output_path="isl_output.mp4"):
    final_clips = []
    for isl_tokens in all_isl_sentences:
        final_clips.extend(isl_tokens_to_clips(isl_tokens))

    if not final_clips:
        return None

    final_video = concatenate_videoclips(final_clips, method="compose")
    final_video.write_videofile(
        output_path, codec="libx264", audio=False, fps=24, logger=None
    )
    return output_path
