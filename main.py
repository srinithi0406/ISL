import spacy
import whisper
from moviepy import VideoFileClip, concatenate_videoclips
import os
import streamlit as st

# =====================================================
# 0. LOAD MODELS (CACHED FOR STREAMLIT)
# =====================================================

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
    video.audio.write_audiofile(audio_path, logger=None)
    return audio_path



def speech_to_text(audio_path):
    result = speech_model.transcribe(audio_path)
    return result["text"]


def video_to_isl(video_path):
    audio_path = extract_audio_from_video(video_path)
    text = speech_to_text(audio_path)

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    all_isl = []
    for s in sentences:
        isl = english_to_isl(s)
        all_isl.append(isl)

    return all_isl

# =====================================================
# 3. ISL TOKENS → VIDEO CLIPS
# =====================================================

ASSET_DIR = "./assets"

DISPLAY_TIME_WORD = 2.5
DISPLAY_TIME_LETTER = 0.8


def isl_tokens_to_clips(isl_tokens):
    clips = []

    for token in isl_tokens:
        token = token.lower()
        video_path = os.path.join(ASSET_DIR, f"{token}.mp4")

        # Word-level sign
        if os.path.exists(video_path):
            clips.append(
                VideoFileClip(video_path).with_duration(DISPLAY_TIME_WORD)
            )
        else:
            # Letter-level fallback
            for ch in token:
                if ch.isalpha():
                    letter_path = os.path.join(ASSET_DIR, f"{ch.upper()}.mp4")
                    if os.path.exists(letter_path):
                        clips.append(
                            VideoFileClip(letter_path).with_duration(DISPLAY_TIME_LETTER)
                        )

    return clips

# =====================================================
# 4. SAVE FINAL ISL VIDEO
# =====================================================

def save_isl_video(all_isl_sentences, output_path="isl_output.mp4"):
    final_clips = []

    for isl_tokens in all_isl_sentences:
        final_clips.extend(isl_tokens_to_clips(isl_tokens))

    if not final_clips:
        return None

    final_video = concatenate_videoclips(final_clips, method="compose")
    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio=False,
        fps=24,
        logger=None
    )

    return output_path
