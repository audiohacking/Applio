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
    
    # Create directories
    for directory in [app_support_dir, logs_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created/verified directory: {directory}")
    
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
    """Wait for the server to be ready by polling the endpoint."""
    print("Waiting for Applio server to start...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=1)
            if response.getcode() == 200:
                print("Applio server is ready!")
                return True
        except (urllib.error.URLError, ConnectionError, OSError):
            # Server not ready yet, wait a bit
            time.sleep(0.5)
    print(f"Warning: Server did not respond within {timeout} seconds")
    return False

def launch_gradio(app_dir, logs_dir):
    """Launch the Gradio app."""
    global _gradio_thread
    
    # Import and run the Gradio app
    sys.path.insert(0, str(app_dir))
    
    # Set up log file to capture all output
    log_file_path = logs_dir / "console.log"
    
    # Custom print wrapper that writes to both stdout and log file
    import builtins
    _original_print = builtins.print
    
    def _logged_print(*args, **kwargs):
        """Print that also writes to log file."""
        # Call original print
        _original_print(*args, **kwargs)
        # Also write to log file
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                from datetime import datetime
                msg = ' '.join(str(arg) for arg in args)
                if msg.strip():
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [INFO] {msg}\n")
                    f.flush()
        except Exception:
            pass
    
    # Replace print temporarily for server thread
    builtins.print = _logged_print
    
    # Run the Gradio app in a thread so pywebview can take control of main thread
    def run_gradio():
        print(f"Starting Applio...")
        print(f"Logs directory: {logs_dir}")
        print(f"Console log file: {log_file_path}")
        
        # Import the app module which will launch Gradio
        import app
    
    _gradio_thread = threading.Thread(target=run_gradio, daemon=True)
    _gradio_thread.start()
    
    # Wait for server to be ready
    wait_for_server()
    
    # Launch pywebview window
    try:
        import webview
        print("Opening Applio window...")
        
        # Create window and keep reference so we can treat close-as-quit
        window = webview.create_window(
            'Applio',
            'http://127.0.0.1:6969',
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(800, 600),
            background_color='#1a1a1a',
            text_select=True,
            on_top=False,  # Keep in foreground but not always on top
            focus=True     # Get focus on creation
        )
        
        # On macOS, closing the window (red X) does not quit the app by default;
        # the Cocoa run loop keeps running and the app can "reopen". Treat window
        # close as an explicit quit: cleanup and exit so we don't respawn.
        if window is not None:
            def on_window_closed():
                print("\nWindow closed by user — quitting.")
                cleanup()
                os._exit(0)
            try:
                window.events.closed += on_window_closed
            except Exception:
                pass  # older pywebview may not have events.closed
        
        # Register cleanup handler for graceful shutdown (e.g. Dock Quit, SIGTERM)
        atexit.register(cleanup)
        
        # Start the webview - this blocks until the GUI run loop exits
        # When window is closed, on_window_closed() runs and we os._exit(0)
        webview.start(gui='cocoa')  # Explicitly use Cocoa for macOS
        
        # If start() returns without on_window_closed firing (e.g. other backends)
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
