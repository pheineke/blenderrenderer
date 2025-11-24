import os
import subprocess
from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RENDER_FOLDER'] = 'renders'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RENDER_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        
        if file and file.filename.endswith('.blend'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            render_type = request.form.get('render_type')
            output_filename = f"{os.path.splitext(filename)[0]}_render"
            output_path = os.path.join(app.config['RENDER_FOLDER'], output_filename)
            
            # Basic Blender command structure
            # blender -b <file> -o <output> -f 1 (for image) or -a (for animation)
            # Note: This assumes 'blender' is in PATH. 
            
            cmd = ['blender', '-b', filepath, '-o', output_path]
            
            if render_type == 'animation':
                cmd.append('-a')
                # For animation, blender adds frame numbers. We might need to zip or handle multiple files.
                # For simplicity in this MVP, let's assume it outputs a video file if configured in the blend file,
                # or we might just serve the first frame if it's a sequence.
                # A safer bet for a generic "render animation" is that the user has set up the output format in the blend file.
                # However, -o overrides the output path.
                # Let's stick to image for the MVP default or handle single frame render for 'image' type.
            else:
                # Render frame 1
                cmd.extend(['-f', '1'])
                # Blender appends frame number to output, e.g., output_render0001.png
                # We need to find the generated file.
            
            try:
                subprocess.run(cmd, check=True)
            except FileNotFoundError:
                return "Blender executable not found. Please ensure Blender is installed and in your PATH."
            except subprocess.CalledProcessError:
                return "Error during rendering."

            # Find the rendered file
            # This is tricky because we don't know the exact extension or if it added frame numbers.
            # We'll search the render folder for the newest file matching our pattern.
            
            # For now, let's redirect to a download page or just try to download the likely file.
            # Let's list files in render folder and pick the one starting with output_filename
            
            rendered_files = [f for f in os.listdir(app.config['RENDER_FOLDER']) if f.startswith(output_filename)]
            if rendered_files:
                # Return the first match (likely the only one for image)
                return redirect(url_for('download_file', filename=rendered_files[0]))
            else:
                return "Rendered file not found."

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['RENDER_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
