#!/usr/bin/env python
"""
Run Django development server with HTTPS support
"""
import os
import sys
import subprocess
from pathlib import Path

def run_https_server():
    # Check if we have the required packages
    try:
        import django_extensions
        import werkzeug
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please run: pip install django-extensions Werkzeug pyOpenSSL")
        return
    
    # Generate self-signed certificate if it doesn't exist
    cert_file = Path("cert.crt")
    key_file = Path("cert.key")
    
    if not cert_file.exists() or not key_file.exists():
        print("Generating self-signed certificate...")
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-keyout", "cert.key", 
            "-out", "cert.crt", "-days", "365", "-nodes",
            "-subj", "/C=US/ST=CA/L=SF/O=Dev/CN=127.0.0.1"
        ], check=True)
        print("Certificate generated successfully!")
    
    # Run the HTTPS server
    print("Starting HTTPS development server...")
    print("Access your app at: https://127.0.0.1:8001/")
    print("Note: Your browser may show a security warning - click 'Advanced' and 'Proceed to 127.0.0.1'")
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        subprocess.run([
            sys.executable, "manage.py", "runserver_plus", 
            "--cert-file", "cert.crt", "--key-file", "cert.key",
            "--threaded", "127.0.0.1:8001"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    run_https_server()