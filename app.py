from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import queue
import threading
from realtime import RealtimeTranslator
from main import video_to_isl, audio_to_isl, text_to_isl, save_isl_video

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'temp'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global translator instance
translator = None
translation_active = False

# Ensure temp directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Callbacks for real-time updates
def on_transcript_received(text):
    """Called when new transcript is available"""
    socketio.emit('transcript_update', {'text': text})
    print(f"[TRANSCRIPT] Emitted: {text}")

def on_isl_text_received(text):
    """Called when new ISL text is available"""
    socketio.emit('isl_update', {'text': text})
    print(f"[ISL] Emitted: {text}")

def video_monitor_thread():
    """Monitor video queue and emit video paths to client"""
    global translator, translation_active
    
    print("[VIDEO MONITOR] Thread started")
    
    while translation_active:
        try:
            if translator and not translator.video_queue.empty():
                video_path, duration = translator.video_queue.get(timeout=0.5)
                
                if video_path and os.path.exists(video_path):
                    # Get relative path for web serving
                    rel_path = os.path.relpath(video_path, os.getcwd())
                    
                    socketio.emit('video_update', {
                        'path': '/' + rel_path.replace('\\', '/'),
                        'duration': duration,
                        'filename': os.path.basename(video_path)
                    })
                    print(f"[VIDEO] Emitted: {os.path.basename(video_path)}")
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[ERROR] Video monitor: {e}")
    
    print("[VIDEO MONITOR] Thread stopped")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/start_realtime', methods=['POST'])
def start_realtime():
    """Start real-time translation"""
    global translator, translation_active
    
    try:
        # Create new translator instance
        translator = RealtimeTranslator()
        
        # Set up callbacks
        translator.on_transcript = on_transcript_received
        translator.on_isl_text = on_isl_text_received
        
        # Start translator
        translator.start()
        translation_active = True
        
        # Start video monitor thread
        video_thread = threading.Thread(target=video_monitor_thread, daemon=True)
        video_thread.start()
        
        return jsonify({'success': True, 'message': 'Real-time translation started'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stop_realtime', methods=['POST'])
def stop_realtime():
    """Stop real-time translation"""
    global translator, translation_active
    
    try:
        translation_active = False
        
        if translator:
            translator.stop()
            translator = None
        
        return jsonify({'success': True, 'message': 'Real-time translation stopped'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/process_text', methods=['POST'])
def process_text():
    """Process text input"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Convert to ISL
        isl_sentences = text_to_isl(text)
        
        if isl_sentences:
            # Generate video
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'isl_translation.mp4')
            save_isl_video(isl_sentences, output_path)
            
            # Get ISL tokens
            isl_text = " | ".join([" ".join(s) for s in isl_sentences])
            
            return jsonify({
                'success': True,
                'isl_text': isl_text,
                'video_path': '/download/isl_translation.mp4'
            })
        else:
            return jsonify({'success': False, 'error': 'Translation failed'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/process_file', methods=['POST'])
def process_file():
    """Process video or audio file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('type', 'audio')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process based on type
        if file_type == 'video':
            isl_sentences = video_to_isl(filepath)
        else:
            isl_sentences = audio_to_isl(filepath)
        
        if isl_sentences:
            # Generate ISL video
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'isl_translation.mp4')
            save_isl_video(isl_sentences, output_path)
            
            # Get ISL tokens
            isl_text = " | ".join([" ".join(s) for s in isl_sentences])
            
            return jsonify({
                'success': True,
                'isl_text': isl_text,
                'video_path': '/download/isl_translation.mp4'
            })
        else:
            return jsonify({'success': False, 'error': 'Translation failed'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated ISL video"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found", 404

@app.route('/assets/<path:filename>')
def serve_asset(filename):
    """Serve asset files (ISL videos)"""
    filepath = os.path.join('assets', filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return "File not found", 404

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)