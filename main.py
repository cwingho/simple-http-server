#!/usr/bin/env python3
import os
import sys
import argparse
from http.server import ThreadingHTTPServer
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
    
    # Ensure directories exist
    for dir_name in ["data", "static", "templates"]:
        dir_path = os.path.join(directory, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created {dir_name} directory: {dir_path}")
    
    # Create the server
    handler = UploadEnabledHTTPHandler
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True  # Set daemon threads
    
    # Print server information
    data_dir = os.path.join(directory, "data")
    print(f"Serving HTTP on {host} port {port} (http://{host if host != '0.0.0.0' else 'localhost'}:{port}/) ...")
    print(f"Base directory: {os.path.abspath(directory)}")
    print(f"Accessible directory: {os.path.abspath(data_dir)}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()
        server.server_close()
        print("Server stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        server.shutdown()
        server.server_close()
        sys.exit(1)

if __name__ == "__main__":
    args = parse_arguments()
    run_server(args.host, args.port, args.directory) 