import subprocess
import time
import sys
import os
import threading
import socket
from pathlib import Path

def get_free_port():
    """Finds an unused port on localhost."""
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_http_server(directory, port):
    """Starts Python's built-in HTTP server in a background thread."""
    print(f"[Tunnel] Starting HTTP Server on port {port} for directory {directory}...")
    
    # We run http.server via subprocess so we can terminate it later easily
    server_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=directory,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return server_process

def start_localtunnel(port):
    """Starts localtunnel via npx and captures the public HTTPS URL."""
    print(f"[Tunnel] Exposing port {port} to localtunnel...")
    
    try:
        # Start npx localtunnel
        process = subprocess.Popen(
            ["npx", "localtunnel", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Read stdout line by line until we find the public URL
        url = None
        start_time = time.time()
        
        # Poll for URL (usually outputs within 5-10 seconds)
        while time.time() - start_time < 30:
            line = process.stdout.readline()
            if not line:
                break
                
            print(f"[localtunnel stdout] {line.strip()}")
            
            # localtunnel output format: "your url is: https://xxxx.loca.lt"
            if "your url is:" in line:
                url = line.split("your url is:")[-1].strip()
                break
                
            time.sleep(0.5)
            
        if url:
            return process, url
        else:
            process.terminate()
            return None, "Error: Could not retrieve URL from localtunnel output."
            
    except Exception as e:
        return None, f"Error launching npx localtunnel: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python tunnel_manager.py <project_directory> [port]")
        sys.exit(1)
        
    directory = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else get_free_port()
    
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
        
    # 1. Start Web Server
    server_proc = run_http_server(directory, port)
    
    # Give server a second to bind to port
    time.sleep(1.5)
    
    # 2. Expose via localtunnel
    tunnel_proc, tunnel_url = start_localtunnel(port)
    
    if tunnel_proc:
        print("\n==================================================")
        print(f"🎉 PUBLIC TUNNEL ESTABLISHED! 🎉")
        print(f"👉 URL: {tunnel_url}")
        print("==================================================")
        print("Press Ctrl+C to close the tunnel and server.")
        
        try:
            # Keep running until container or parent process exits
            # In a real environment, we'd log this URL and keep the process alive
            while True:
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nShutting down tunnel services...")
        finally:
            tunnel_proc.terminate()
            server_proc.terminate()
    else:
        # Clean up server
        server_proc.terminate()
        print(f"\n❌ Tunnel setup failed: {tunnel_url}")
        print("Tip: Make sure Node.js (npx) is installed on your host system if executing locally.")

if __name__ == "__main__":
    main()
