import pyaudio
import queue
import threading
from google.cloud import speech
import spacy
import os
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time

# --- Configuration ---
RATE = 16000
CHUNK = int(RATE / 10)
ASSET_DIR = "./assets"

# --- NLP Model ---
print("[INFO] Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")

# --- Video Processing ---
def get_video_duration(path):
    """Gets duration of video file in seconds."""
    if not os.path.exists(path):
        return 0
    try:
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return duration
    except Exception as e:
        print(f"[ERROR] Could not get duration for {path}: {e}")
        return 0

# --- ISL Conversion Logic ---
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
    doc = nlp(sentence)
    condition_tokens, main_tokens = split_clauses(doc)
    condition_isl = process_clause(condition_tokens)
    main_isl = process_clause(main_tokens)
    final_isl = condition_isl + [","] + main_isl if condition_isl else main_isl
    return final_isl

def isl_tokens_to_clip_paths(isl_tokens):
    """Maps ISL tokens to video file paths."""
    clip_paths = []
    for token in isl_tokens:
        token = token.lower()
        video_path = os.path.join(ASSET_DIR, f"{token}.mp4")
        if os.path.exists(video_path):
            clip_paths.append(video_path)
        else:
            for ch in token:
                if ch.isalpha():
                    letter_path = os.path.join(ASSET_DIR, f"{ch.upper()}.mp4")
                    if os.path.exists(letter_path):
                        clip_paths.append(letter_path)
    return clip_paths

# --- Microphone Stream ---
class MicrophoneStream:
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b''.join(data)

# --- Real-time Translator ---
class RealtimeTranslator:
    def __init__(self):
        self.text_queue = queue.Queue()
        self.video_queue = queue.Queue(maxsize=10)  # Buffer for smooth playback
        self._stop_event = threading.Event()
        self._threads = []
        
        # Callbacks for UI updates
        self.on_transcript = None
        self.on_isl_text = None

    def start(self):
        self._stop_event.clear()
        
        # Start speech-to-text thread
        speech_thread = threading.Thread(target=self._run_speech_to_text, daemon=True)
        speech_thread.start()
        self._threads.append(speech_thread)
        
        # Start ISL conversion thread
        isl_thread = threading.Thread(target=self._run_isl_conversion, daemon=True)
        isl_thread.start()
        self._threads.append(isl_thread)

    def stop(self):
        print("[INFO] Stopping translator...")
        self._stop_event.set()
        self.text_queue.put(None)
        self.video_queue.put(None)

    def _run_speech_to_text(self):
        """Speech recognition thread."""
        language_code = 'en-US'
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=language_code,
            enable_automatic_punctuation=True
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=False
        )

        try:
            with MicrophoneStream(RATE, CHUNK) as stream:
                audio_generator = stream.generator()
                requests = (speech.StreamingRecognizeRequest(audio_content=content)
                            for content in audio_generator)
                responses = client.streaming_recognize(streaming_config, requests)
                
                for response in responses:
                    if self._stop_event.is_set():
                        break
                    if not response.results:
                        continue

                    result = response.results[0]
                    if not result.alternatives:
                        continue
                    
                    transcript = result.alternatives[0].transcript.strip()
                    
                    if result.is_final and transcript:
                        print(f"[TRANSCRIPT] {transcript}")
                        if self.on_transcript:
                            self.on_transcript(transcript)
                        self.text_queue.put(transcript)
                        
        except Exception as e:
            print(f"[ERROR] Speech recognition error: {e}")

    def _run_isl_conversion(self):
        """ISL conversion and video queueing thread."""
        print("[INFO] ISL conversion thread started")
        
        while not self._stop_event.is_set():
            try:
                sentence = self.text_queue.get(timeout=1)
                if sentence is None:
                    break
                
                print(f"[ISL] Processing: {sentence}")
                
                # Convert to ISL
                isl_tokens = english_to_isl(sentence)
                isl_text = " ".join(isl_tokens)
                print(f"[ISL] Tokens: {isl_text}")
                
                if self.on_isl_text:
                    self.on_isl_text(isl_text)
                
                # Get video clips
                clip_paths = isl_tokens_to_clip_paths(isl_tokens)
                
                if not clip_paths:
                    print("[ISL] No clips found")
                    continue
                
                # Queue videos with durations
                for path in clip_paths:
                    duration = get_video_duration(path)
                    if duration > 0:
                        self.video_queue.put((path, duration))
                        print(f"[ISL] Queued: {os.path.basename(path)} ({duration:.2f}s)")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] ISL conversion error: {e}")

# --- GUI Application ---
class ISLVideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-time Speech to ISL")
        self.root.geometry("900x700")
        self.root.configure(bg='#2b2b2b')
        
        # Translator
        self.translator = RealtimeTranslator()
        self.translator.on_transcript = self.update_transcript #type: ignore
        self.translator.on_isl_text = self.update_isl_text #type: ignore
        
        # Video playback
        self.current_cap = None
        self.is_playing = False
        self.playback_thread = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Title
        title = tk.Label(self.root, text="🎤 Real-time Speech to ISL Video", 
                        font=('Arial', 20, 'bold'), bg='#2b2b2b', fg='white')
        title.pack(pady=10)
        
        # Video display
        video_frame = tk.Frame(self.root, bg='#1a1a1a', relief=tk.SUNKEN, bd=2)
        video_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.video_label = tk.Label(video_frame, bg='#1a1a1a', 
                                    text="Video will appear here", 
                                    fg='gray', font=('Arial', 14))
        self.video_label.pack(expand=True)
        
        # Transcript area
        transcript_frame = tk.LabelFrame(self.root, text="English Transcript", 
                                        font=('Arial', 12, 'bold'),
                                        bg='#2b2b2b', fg='white')
        transcript_frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.transcript_text = tk.Text(transcript_frame, height=3, wrap=tk.WORD,
                                      font=('Arial', 11), bg='#3a3a3a', fg='white',
                                      insertbackground='white')
        self.transcript_text.pack(padx=5, pady=5, fill=tk.X)
        
        # ISL text area
        isl_frame = tk.LabelFrame(self.root, text="ISL Tokens", 
                                 font=('Arial', 12, 'bold'),
                                 bg='#2b2b2b', fg='white')
        isl_frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.isl_text = tk.Text(isl_frame, height=2, wrap=tk.WORD,
                               font=('Arial', 11, 'bold'), bg='#3a3a3a', 
                               fg='#4CAF50', insertbackground='white')
        self.isl_text.pack(padx=5, pady=5, fill=tk.X)
        
        # Control buttons
        btn_frame = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame.pack(pady=10)
        
        self.start_btn = tk.Button(btn_frame, text="▶ Start", command=self.start,
                                   font=('Arial', 12, 'bold'), bg='#4CAF50', 
                                   fg='white', padx=20, pady=10, cursor='hand2')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ Stop", command=self.stop,
                                  font=('Arial', 12, 'bold'), bg='#f44336', 
                                  fg='white', padx=20, pady=10, cursor='hand2',
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(self.root, text="Ready", 
                                     font=('Arial', 10), bg='#2b2b2b', fg='gray')
        self.status_label.pack(pady=5)
        
    def start(self):
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="🎙️ Listening...", fg='#4CAF50')
        
        # Start translator
        self.translator.start()
        
        # Start video playback
        self.is_playing = True
        self.playback_thread = threading.Thread(target=self._play_videos, daemon=True)
        self.playback_thread.start()
        
    def stop(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped", fg='gray')
        
        self.is_playing = False
        self.translator.stop()
        
        if self.current_cap:
            self.current_cap.release()
            
    def update_transcript(self, text):
        """Update transcript display."""
        self.transcript_text.insert(tk.END, text + " ")
        self.transcript_text.see(tk.END)
        
    def update_isl_text(self, text):
        """Update ISL text display."""
        self.isl_text.insert(tk.END, text + " | ")
        self.isl_text.see(tk.END)
        
    def _play_videos(self):
        """Video playback thread - plays videos from queue."""
        print("[VIDEO] Playback thread started")
        
        while self.is_playing:
            try:
                # Get next video from queue
                video_data = self.translator.video_queue.get(timeout=0.5)
                if video_data is None:
                    break
                    
                video_path, duration = video_data
                print(f"[VIDEO] Playing: {os.path.basename(video_path)}")
                
                # Play video
                self._play_single_video(video_path)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] Video playback error: {e}")
                
    def _play_single_video(self, video_path):
        """Play a single video file."""
        cap = cv2.VideoCapture(video_path)
        self.current_cap = cap
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30
        delay = int(1000 / fps)
        
        while cap.isOpened() and self.is_playing:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize to fit display
            frame = cv2.resize(frame, (640, 480))
            
            # Convert to ImageTk
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update label
            self.video_label.imgtk = imgtk #type: ignore
            self.video_label.configure(image=imgtk)
            
            # Maintain frame rate
            time.sleep(delay / 1000.0)
            
        cap.release()
        self.current_cap = None

# --- Main Entry Point ---
def main():
    root = tk.Tk()
    app = ISLVideoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()