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

if __name__ == "__main__":
    args = parse_arguments()
    run_server(args.host, args.port, args.directory) 