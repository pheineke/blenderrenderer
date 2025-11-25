# Blender Render Server

A simple Flask-based web server that allows users to upload `.blend` files and render them on a remote server.

## Features

- **File Upload**: Upload `.blend` files via a web interface.
- **Rendering**: Supports rendering single images (Frame 1) or animations.
- **Automatic Setup**: The `wrapper.py` script handles dependency management.
    - Checks for Blender installation.
    - Downloads Blender 4.3.0 (Linux x64) automatically if missing.
- **Tunneling**: Integrated support for `cloudflared` to expose the local server to the internet.

## Prerequisites

- **OS**: Linux (for the automatic Blender download/execution logic).
- **Python**: 3.x with `flask` and `requests` installed.
- **Cloudflared**: Binary expected at `./cloudflared/cloudflared-linux-amd64` (if using the wrapper).

## Installation & Usage

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd blenderrender
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install flask requests
    ```

3.  **Run the Server**:
    Use the wrapper script to handle everything automatically:
    ```bash
    python wrapper.py
    ```
    
    This script will:
    - Download Blender 4.3.0 if not found.
    - Start a Cloudflared tunnel (and print the URL).
    - Start the Flask server on port 5000.

4.  **Access**:
    Open the printed Cloudflared URL or `http://localhost:5000` in your browser.

## Persistent URL (Optional)

To use a persistent Cloudflare Tunnel URL:
1.  Create a tunnel in the Cloudflare Dashboard.
2.  Get the tunnel token.
3.  Either:
    - Set the `TUNNEL_TOKEN` environment variable.
    - OR create a file named `tunnel_token` in the project root containing the token.
4.  Run `wrapper.py` as usual. It will detect the token and start the named tunnel.

## Code Explanation

### `app.py`
The core Flask application responsible for handling web requests and rendering logic.
- **Routes**:
  - `GET /`: Renders the upload form (`templates/index.html`).
  - `POST /`: Handles file upload.
    - Saves the uploaded `.blend` file to the `uploads/` directory.
    - Constructs the Blender command line arguments based on user selection (Image vs Animation).
    - Executes Blender using `subprocess` in background mode (`-b`).
    - Redirects to the download route upon success.
  - `GET /download/<filename>`: Serves the rendered file from the `renders/` directory.
- **Configuration**:
  - `BLENDER_PATH`: Environment variable used to specify the Blender executable location. Defaults to `blender`.

### `wrapper.py`
An automation script designed to simplify deployment on a Linux server.
1.  **Blender Setup**:
    - Checks if `blender` is available in the system `PATH`.
    - If not found, checks the local `blender-bin/` directory.
    - If still missing, downloads the official Blender 4.3.0 Linux binary, extracts it, and sets the `BLENDER_PATH` environment variable.
2.  **Cloudflared Tunnel**:
    - Checks for the `cloudflared` binary at `./cloudflared/cloudflared-linux-amd64`.
    - Starts a tunnel for `localhost:5000`.
    - Monitors the process output to capture and print the public `.trycloudflare.com` URL to the console.
3.  **Server Execution**:
    - Launches `app.py` as a subprocess.
    - Handles graceful shutdown of both the server and the tunnel.

### Directory Structure
- `templates/`: Contains HTML templates (currently just `index.html`).
- `uploads/`: Temporary storage for uploaded `.blend` files.
- `renders/`: Storage for the output rendered images/videos.
- `blender-bin/`: Created by `wrapper.py` to store the downloaded Blender binaries.
