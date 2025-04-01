#!/usr/bin/env python3
import os
import sys
import argparse
from http.server import HTTPServer
from server import UploadEnabledHTTPHandler

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Simple HTTP Server with file upload/download capability'
    )
    parser.add_argument(
        '-p', '--port', 
        type=int, 
        default=8000,
        help='Port to listen on (default: 8000)'
    )
    parser.add_argument(
        '-H', '--host',
        type=str,
        default='0.0.0.0',
        help='Host address to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        'directory', 
        nargs='?', 
        default=os.getcwd(),
        help='Base directory (server will only serve ./data/ subdirectory)'
    )
    return parser.parse_args()

def run_server(host, port, directory):
    """Run the HTTP server."""
    # Change to the specified directory
    os.chdir(directory)
    
    # Ensure data directory exists
    data_dir = os.path.join(directory, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"Created data directory: {data_dir}")
    
    # Ensure static directory exists
    static_dir = os.path.join(directory, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
        print(f"Created static directory: {static_dir}")
    
    # Ensure templates directory exists
    templates_dir = os.path.join(directory, "templates")
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir, exist_ok=True)
        print(f"Created templates directory: {templates_dir}")
    
    # Create the server
    handler = UploadEnabledHTTPHandler
    server = HTTPServer((host, port), handler)
    
    # Print server information
    print(f"Serving HTTP on {host} port {port} (http://{host if host != '0.0.0.0' else 'localhost'}:{port}/) ...")
    print(f"Base directory: {os.path.abspath(directory)}")
    print(f"Accessible directory: {os.path.abspath(data_dir)}")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start the server
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()

def create_default_static_files(static_dir):
    """Create default static files if they don't exist."""
    # Create CSS file
    css_path = os.path.join(static_dir, "style.css")
    if not os.path.exists(css_path):
        with open(css_path, 'w') as f:
            f.write("""/* Default styles */
:root {
    --background: #ffffff;
    --foreground: #09090b;
    --card: #f4f4f5;
    --card-foreground: #09090b;
    --primary: #18181b;
    --primary-foreground: #ffffff;
    --secondary: #f4f4f5;
    --secondary-foreground: #18181b;
    --muted: #f4f4f5;
    --muted-foreground: #71717a;
    --border: #e4e4e7;
    --input: #e4e4e7;
    --radius: 0.5rem;
}

/* Base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background-color: var(--background);
    color: var(--foreground);
    line-height: 1.5;
    padding: 1.5rem;
    max-width: 1200px;
    margin: 0 auto;
}

/* Add more styles as needed */
""")
        print(f"Created default CSS file: {css_path}")
    
    # Create JS file
    js_path = os.path.join(static_dir, "script.js")
    if not os.path.exists(js_path):
        with open(js_path, 'w') as f:
            f.write("""// Default script
document.addEventListener('DOMContentLoaded', function() {
    console.log('File server loaded');
    
    // Add your JavaScript here
});
""")
        print(f"Created default JS file: {js_path}")

if __name__ == "__main__":
    args = parse_arguments()
    run_server(args.host, args.port, args.directory) 