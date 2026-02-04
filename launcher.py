#!/usr/bin/env python3
"""
Applio macOS Launcher
This script is the entry point for the PyInstaller-bundled macOS app.
It sets up the environment and launches Applio with pywebview.
"""

import os
import sys
import time
import threading
from pathlib import Path
import socket
import urllib.request
import urllib.error
import atexit

# Single instance lock port
SINGLE_INSTANCE_PORT = 58766

# Global references for cleanup
_gradio_thread = None
_lock_socket = None
_cleanup_done = False

def setup_environment():
    """Set up the macOS app environment."""
    # Determine if we're running as a bundled app
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        bundle_dir = sys._MEIPASS
        app_dir = Path(bundle_dir)
        print(f"Running as bundled app from: {bundle_dir}")
    else:
        # Running as script
        app_dir = Path(__file__).parent
        print(f"Running as script from: {app_dir}")
    
    # Set up paths for the app - ALL data goes to user's Library directory
    home_dir = Path.home()
    app_support_dir = home_dir / "Library" / "Application Support" / "Applio"
    logs_dir = home_dir / "Library" / "Logs" / "Applio"
    
    # Create directories (user data root so models/data persist across builds/versions)
    (app_support_dir / "logs").mkdir(parents=True, exist_ok=True)
    for directory in [app_support_dir, logs_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created/verified directory: {directory}")
    
    os.environ["APPLIO_APP_SUPPORT"] = str(app_support_dir)
    
    # IMPORTANT: Set environment variables for Apple MPS optimization
    # These settings optimize for Apple's unified memory architecture
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"  # Enable Metal Performance Shaders with CPU fallback
    os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"  # Disable MPS memory limit to prevent OOM errors
    os.environ["OMP_NUM_THREADS"] = "1"  # Optimize for single-threaded performance on Apple Silicon
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Allow duplicate library loading
    
    # Additional MPS optimizations for Apple Silicon
    if sys.platform == "darwin":
        # Note: These are experimental optimizations for Metal GPU performance
        # METAL_DEVICE_WRAPPER_TYPE enables Metal device wrapper for better compatibility
        os.environ["METAL_DEVICE_WRAPPER_TYPE"] = "1"
    
    # Change working directory to app bundle
    os.chdir(app_dir)
    print(f"Changed working directory to: {os.getcwd()}")
    
    print(f"\nApplio Data directories configured:")
    print(f"  App Support: {app_support_dir}")
    print(f"  Logs: {logs_dir}")
    print(f"  Working Dir: {app_dir}")
    
    # Log system information
    import platform
    print(f"\nSystem Information:")
    print(f"  Platform: {sys.platform}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    
    # Check for Apple Silicon
    if sys.platform == "darwin" and platform.machine() == "arm64":
        print(f"  Apple Silicon: Detected (MPS optimizations enabled)")
    
    return app_dir, logs_dir

def check_single_instance():
    """Check if another instance of the app is already running."""
    # Try to bind to a port to ensure single instance
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        return sock  # Keep socket open to maintain lock
    except OSError:
        # Port is already in use - another instance is running
        return None

def cleanup():
    """Cleanup resources on shutdown. Idempotent - safe to call multiple times."""
    global _lock_socket, _cleanup_done
    
    # Prevent multiple cleanup calls
    if _cleanup_done:
        return
    _cleanup_done = True
    
    print("\nCleaning up resources...")
    
    # Close the lock socket
    if _lock_socket:
        try:
            _lock_socket.close()
            print("✓ Released instance lock")
        except (OSError, Exception):
            pass
    
    # Note: Gradio thread is daemon and will be terminated automatically
    print("✓ Server shutdown initiated")
    print("Goodbye!")

def wait_for_server(url='http://127.0.0.1:6969', timeout=30):
    """Wait for the server to be ready by polling. Returns True when ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=1)
            if response.getcode() == 200:
                return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.5)
    return False

# Shown immediately so user sees progress; we redirect to the real UI when server is up (no second instance).
LOADING_HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Applio - Starting</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #1a1a1a; color: #e5e5e5; margin: 0; padding: 2rem; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; }
  .box { max-width: 520px; text-align: center; }
  h1 { font-size: 1.5rem; margin-bottom: 1rem; }
  p { color: #a3a3a3; line-height: 1.6; margin: 0.5rem 0; }
  .spinner { width: 40px; height: 40px; border: 3px solid #333; border-top-color: #0ea5e9; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 1.5rem; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .log-path { font-size: 0.85rem; word-break: break-all; color: #737373; margin-top: 1.5rem; }
</style>
</head>
<body>
  <div class="box">
    <div class="spinner"></div>
    <h1>Applio is starting</h1>
    <p>Checking and downloading prerequisites if needed. This may take several minutes on first run.</p>
    <p>You will be switched to the main interface when ready.</p>
    <p class="log-path">Log: ~/Library/Logs/Applio/console.log</p>
  </div>
</body>
</html>'''

def launch_gradio(app_dir, logs_dir):
    """Launch the Gradio app."""
    global _gradio_thread
    
    # Import and run the Gradio app
    sys.path.insert(0, str(app_dir))
    
    # Set up log file to capture all output
    log_file_path = logs_dir / "console.log"
    
    # Custom output wrapper that writes to both stdout and log file
    class TeeOutput:
        """A class that writes to both stdout/stderr and a log file."""
        def __init__(self, file_path, original_stream):
            self.file_path = file_path
            self.original_stream = original_stream
            self.log_file = None
            
        def write(self, message):
            # Write to original stream (stdout/stderr)
            if self.original_stream:
                try:
                    self.original_stream.write(message)
                    self.original_stream.flush()
                except Exception:
                    pass
            
            # Write to log file
            if message.strip():  # Only write non-empty messages
                try:
                    # Open in append mode, write, and close immediately for real-time updates
                    with open(self.file_path, 'a', encoding='utf-8') as f:
                        from datetime import datetime
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        f.write(f"[{timestamp}] {message}")
                        if not message.endswith('\n'):
                            f.write('\n')
                        f.flush()
                except Exception as e:
                    # Fallback to original stream if logging fails
                    if self.original_stream:
                        self.original_stream.write(f"[Logging Error: {e}]\n")
        
        def flush(self):
            if self.original_stream:
                try:
                    self.original_stream.flush()
                except Exception:
                    pass
        
        def isatty(self):
            """Required by uvicorn/logging when configuring formatters; we are not a TTY."""
            return False
    
    # Redirect stdout and stderr to our tee
    sys.stdout = TeeOutput(log_file_path, sys.stdout)
    sys.stderr = TeeOutput(log_file_path, sys.stderr)
    
    print(f"Starting Applio...")
    print(f"Logs directory: {logs_dir}")
    print(f"Console log file: {log_file_path}")
    print(f"All output will be captured to the Console tab in the UI")
    print("=" * 60)
    
    # Single background thread: import app (runs prerequisites) then start Gradio server.
    # We never start a second Applio process.
    def run_app_and_server():
        try:
            import app
            app.launch_gradio("127.0.0.1", 6969)
        except Exception as e:
            print(f"ERROR: Failed to start Applio: {e}")
            import traceback
            traceback.print_exc()
    
    _gradio_thread = threading.Thread(target=run_app_and_server, daemon=True)
    _gradio_thread.start()
    
    try:
        import webview
        print("Opening Applio window (loading page first)...")
        # Show loading page immediately; redirect to real UI when server is ready (no second instance).
        window = webview.create_window(
            'Applio',
            html=LOADING_HTML,
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(800, 600),
            background_color='#1a1a1a',
            text_select=True,
            on_top=False,
            focus=True,
        )
        
        # Redirect this same window when server is up (long timeout for first-run download).
        def redirect_when_ready():
            print("Waiting for Applio server (prerequisites may be downloading)...")
            if wait_for_server(timeout=600):
                print("Applio server is ready — switching to main interface.")
                try:
                    window.load_url("http://127.0.0.1:6969")
                except Exception as e:
                    print(f"Redirect failed: {e}")
            else:
                print("Server did not start in time. Check ~/Library/Logs/Applio/console.log")
        
        threading.Thread(target=redirect_when_ready, daemon=True).start()
        
        # Quit fully on close so macOS does not reopen the app.
        if window is not None:
            def on_window_closed():
                print("\nWindow closed — quitting.")
                cleanup()
                os._exit(0)
            try:
                window.events.closed += on_window_closed
            except Exception:
                pass
        
        atexit.register(cleanup)
        webview.start(gui='cocoa')
        print("\nWindow closed by user")
        
    except ImportError:
        print("Warning: pywebview not available, falling back to browser")
        import webbrowser
        webbrowser.open("http://127.0.0.1:6969")
        # Keep the server running - wait for user to terminate
        print("Server is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
    except Exception as e:
        print(f"Error launching window: {e}")
        print("Falling back to browser...")
        import webbrowser
        webbrowser.open("http://127.0.0.1:6969")
        # Keep the server running - wait for user to terminate
        print("Server is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")

def main():
    """Main entry point."""
    global _lock_socket
    
    try:
        # Check if another instance is already running
        _lock_socket = check_single_instance()
        if _lock_socket is None:
            print("Another instance of Applio is already running.")
            print("Only one instance can be opened at a time.")
            sys.exit(0)
        
        app_dir, logs_dir = setup_environment()
        launch_gradio(app_dir, logs_dir)
        
        # If we reach here, the window was closed gracefully
        # cleanup() will be called by atexit
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\nShutting down Applio...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting Applio: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
