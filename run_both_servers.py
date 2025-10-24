#!/usr/bin/env python
"""
Run both HTTP and HTTPS Django development servers
"""
import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def run_http_server():
    """Run regular HTTP server on port 8000"""
    print("Starting HTTP server on http://127.0.0.1:8000/")
    subprocess.run([sys.executable, "manage.py", "runserver", "127.0.0.1:8000"])

def run_https_server():
    """Run HTTPS server on port 8001"""
    print("Starting HTTPS server on https://127.0.0.1:8001/")
    subprocess.run([
        sys.executable, "manage.py", "runserver_plus", 
        "--cert-file", "cert.crt", "--key-file", "cert.key",
        "127.0.0.1:8001"
    ])

def main():
    print("Starting both HTTP and HTTPS development servers...")
    print("HTTP:  http://127.0.0.1:8000/")
    print("HTTPS: https://127.0.0.1:8001/")
    print("Press Ctrl+C to stop both servers")
    print("-" * 60)
    
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Small delay to let HTTP server start
    time.sleep(2)
    
    # Start HTTPS server (this will block)
    try:
        run_https_server()
    except KeyboardInterrupt:
        print("\nStopping servers...")

if __name__ == "__main__":
    main()