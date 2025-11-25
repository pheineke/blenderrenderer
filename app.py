import os
import subprocess
import threading
import uuid
import re
import time
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RENDER_FOLDER'] = 'renders'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RENDER_FOLDER'], exist_ok=True)

# Global dictionary to store job status
JOBS = {}

def render_worker(job_id, cmd, output_filename):
    """Background worker to run Blender and track progress."""
    JOBS[job_id]['status'] = 'rendering'
    JOBS[job_id]['progress'] = 0
    
    try:
        # Start subprocess with stdout piped
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Regex to match "Fra:123" or similar progress indicators
        # Blender output example: "Fra:1 Mem:20.0M (Peak 20.0M) | Time:00:00.00 | Mem:0.00M, Peak:0.00M | Scene, ViewLayer | Rendered 0/10 Tiles"
        # We'll look for "Fra:<number>"
        
        for line in process.stdout:
            match = re.search(r'Fra:(\d+)', line)
            if match:
                frame = int(match.group(1))
                # For a single image (frame 1), finding "Fra:1" usually means it's working on it.
                # For animation, we'd need to know total frames to calculate percentage.
                # For MVP, let's just increment progress or set it to a "busy" state.
                # If we assume 100 frames for animation default, we can calc. 
                # But for single image, it goes 0 -> 1 -> done.
                
                # Let's just store the frame number for now, or fake a percentage if we don't know total.
                # If it's an image render (-f 1), it's mostly 0% then 100%.
                
                JOBS[job_id]['current_frame'] = frame
                # Simple fake progress for now: 50% if we see a frame, until done.
                JOBS[job_id]['progress'] = 50 
            
            # Also check for "Saved:" to know a file is done
            if "Saved:" in line:
                JOBS[job_id]['progress'] = 90

        process.wait()
        
        if process.returncode == 0:
            JOBS[job_id]['status'] = 'complete'
            JOBS[job_id]['progress'] = 100
            
            # Find the actual output file
            # Blender appends frame numbers, e.g. output0001.png
            # We search for files starting with the base output name
            rendered_files = [f for f in os.listdir(app.config['RENDER_FOLDER']) if f.startswith(output_filename)]
            if rendered_files:
                # Pick the newest one or just the first one
                JOBS[job_id]['result_file'] = rendered_files[0]
            else:
                JOBS[job_id]['status'] = 'error'
                JOBS[job_id]['error'] = 'Output file not found'
        else:
            JOBS[job_id]['status'] = 'error'
            JOBS[job_id]['error'] = f'Blender exited with code {process.returncode}'
            
    except Exception as e:
        JOBS[job_id]['status'] = 'error'
        JOBS[job_id]['error'] = str(e)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and file.filename.endswith('.blend'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            render_type = request.form.get('render_type')
            output_filename = f"{os.path.splitext(filename)[0]}_render"
            output_path = os.path.join(app.config['RENDER_FOLDER'], output_filename)
            
            blender_executable = os.environ.get('BLENDER_PATH', 'blender')
            cmd = [blender_executable, '-b', filepath, '-o', output_path]
            
            if render_type == 'animation':
                cmd.append('-a')
            else:
                cmd.extend(['-f', '1'])
            
            # Create Job
            job_id = str(uuid.uuid4())
            JOBS[job_id] = {
                'status': 'queued',
                'progress': 0,
                'type': render_type
            }
            
            # Start worker thread
            thread = threading.Thread(target=render_worker, args=(job_id, cmd, output_filename))
            thread.start()
            
            return jsonify({'job_id': job_id})

    return render_template('index.html')

@app.route('/status/<job_id>')
def job_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['RENDER_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
