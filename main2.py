import spacy
import whisper
from moviepy import VideoFileClip, concatenate_videoclips
import os
import cv2
import time

# -----------------------------
# Load models
# -----------------------------
import streamlit as st

@st.cache_resource
def load_models():
    nlp = spacy.load("en_core_web_sm")
    speech_model = whisper.load_model("base")
    return nlp, speech_model

nlp, speech_model = load_models()


# =====================================================
# 1. GRAMMAR-BASED ISL PIPELINE
# =====================================================

def process_clause(tokens):
    time_tokens = []
    object_tokens = []
    subject_tokens = []
    verb_tokens = []
    negation_tokens = []
    modifiers = []

    for token in tokens:
        if token.ent_type_ in ("DATE", "TIME"):
            time_tokens.append(token.text.upper())

        elif token.pos_ in ("ADV", "ADP") and token.text.lower() in (
            "before", "after", "immediately", "now", "later"
        ):
            modifiers.append(token.text.upper())

        elif token.pos_ == "ADV":
            object_tokens.append(token.text.upper())

        elif token.dep_ in ("nsubj", "nsubjpass"):
            if token.text.lower() != "it":
                subject_tokens.append(token.text.upper())

        elif token.pos_ == "VERB":
            verb_tokens.append(token.lemma_.upper())

        elif token.dep_ in ("dobj", "pobj", "attr", "acomp"):
            object_tokens.append(token.text.upper())

        elif token.dep_ == "neg":
            negation_tokens.append("NOT")

    return (
        time_tokens +
        modifiers +
        object_tokens +
        subject_tokens +
        verb_tokens +
        negation_tokens
    )


def split_clauses(doc):
    condition_tokens = set()
    main_tokens = set(doc)

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
    doc = nlp(sentence)
    condition_tokens, main_tokens = split_clauses(doc)
    condition_isl = process_clause(condition_tokens)
    main_isl = process_clause(main_tokens)
    return condition_isl + [","] + main_isl if condition_isl else main_isl

# =====================================================
# 2. VIDEO → AUDIO → TEXT → ISL
# =====================================================

def extract_audio_from_video(video_path, audio_path="temp_audio.wav"):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    return audio_path


def speech_to_text(audio_path):
    result = speech_model.transcribe(audio_path)
    return result["text"]


def video_to_isl(video_path):
    print("\nProcessing video:", video_path)

    audio_path = extract_audio_from_video(video_path)
    print("Audio extracted.")

    text = speech_to_text(audio_path)
    print("Recognized English Text:", text)

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    all_isl = []

    for s in sentences:
        isl = english_to_isl(s)
        print("\nEnglish Sentence:", s)
        print("ISL Output:", isl)
        all_isl.append(isl)

    return all_isl

# =====================================================
# 3. ISL TOKENS → MP4 ANIMATION PLAYER
# =====================================================

ASSET_DIR = "./assets"

DISPLAY_TIME_WORD = 2.5
DISPLAY_TIME_LETTER = 0.8

TARGET_WIDTH = 650
TARGET_HEIGHT = 400


def resize_frame(frame):
    return cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))


def play_video(video_path, max_duration=None):
    cap = cv2.VideoCapture(video_path)
    start = time.time()

    if not cap.isOpened():
        print(f"Failed to open video: {video_path}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = resize_frame(frame)
        cv2.imshow("ISL Translator", frame)

        if cv2.waitKey(30) & 0xFF == 27:
            break

        if max_duration and (time.time() - start > max_duration):
            break

    cap.release()


def spell_word(word):
    for ch in word:
        if not ch.isalpha():
            continue

        letter_path = os.path.join(ASSET_DIR, f"{ch.upper()}.mp4")
        if os.path.exists(letter_path):
            play_video(letter_path, DISPLAY_TIME_LETTER)
        else:
            print(f"Missing letter video: {letter_path}")


def play_isl_sequence(isl_tokens):
    for token in isl_tokens:
        token = token.lower()
        video_path = os.path.join(ASSET_DIR, f"{token}.mp4")

        if os.path.exists(video_path):
            play_video(video_path, DISPLAY_TIME_WORD)
        else:
            spell_word(token)

    cv2.destroyAllWindows()

# =====================================================
# 4. ISL VIDEO SAVING (ADDED ONLY)
# =====================================================

def isl_tokens_to_clips(isl_tokens):
    clips = []

    for token in isl_tokens:
        token = token.lower()
        video_path = os.path.join(ASSET_DIR, f"{token}.mp4")

        if os.path.exists(video_path):
            clips.append(
                VideoFileClip(video_path).with_duration(DISPLAY_TIME_WORD)
            )
        else:
            for ch in token:
                if ch.isalpha():
                    letter_path = os.path.join(ASSET_DIR, f"{ch.upper()}.mp4")
                    if os.path.exists(letter_path):
                        clips.append(
                            VideoFileClip(letter_path).with_duration(DISPLAY_TIME_LETTER)
                        )

    return clips


def save_isl_video(all_isl_sentences, output_path="isl_output.mp4"):
    final_clips = []

    for isl_tokens in all_isl_sentences:
        final_clips.extend(isl_tokens_to_clips(isl_tokens))

    if not final_clips:
        print("No ISL clips found to save.")
        return

    final_video = concatenate_videoclips(final_clips, method="compose")
    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio=False,
        fps=24
    )

    print(f"\n✅ ISL output video saved as: {output_path}")

# =====================================================
# 5. MAIN DRIVER
# =====================================================

if __name__ == "__main__":
    video_file = "sample5.mp4"  # Input video
    isl_sentences = video_to_isl(video_file)

    # SAVE ISL VIDEO
    save_isl_video(isl_sentences, output_path="isl_translation.mp4")

    # OPTIONAL: Play on screen
    for isl in isl_sentences:
        play_isl_sequence(isl)
