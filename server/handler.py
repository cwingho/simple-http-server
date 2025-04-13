import os
import io
import urllib.parse
from http.server import SimpleHTTPRequestHandler
import cgi
from server.path_utils import get_file_info
from server.template_loader import generate_directory_listing

class UploadEnabledHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with file upload capability that restricts access to ./data/."""
    
    # Define the data directory
    data_directory = "data"
    
    # Define content type mappings
    extensions_map = {
        '.html': 'text/html',
        '.htm': 'text/html',
        '.txt': 'text/plain',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.pdf': 'application/pdf',
        '.zip': 'application/zip',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '': 'application/octet-stream',    # Default
    }
    
    def translate_path(self, path):
        """Override translate_path to restrict access to the data directory."""
        # Normalize the URL path
        path = path.split('?', 1)[0].split('#', 1)[0]  # Remove query parameters and fragment
        path = urllib.parse.unquote(path).replace('/', os.sep)
        
        # Make it absolute
        cwd = os.getcwd()
        data_dir = os.path.join(cwd, self.data_directory)
        
        # Ensure data directory exists
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        # If it's the root path, return data directory
        if not path or path == '/':
            return data_dir
        
        # Remove any leading separator and join with data directory
        while path.startswith(os.sep):
            path = path[1:]
        
        full_path = os.path.normpath(os.path.join(data_dir, path))
        
        # Ensure the path is still within data directory
        return full_path if full_path.startswith(data_dir) else data_dir
    
    def _prepare_directory_items(self, path):
        """Prepare directory items for listing with sorting."""
        try:
            # Get list of directory contents
            file_list = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None, None, None, None
        
        # Get query parameters for sorting
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        sort_by = query_components.get('sort', ['name'])[0]
        sort_order = query_components.get('order', ['asc'])[0]
        
        # Get display path
        display_path = urllib.parse.unquote(self.path).split('?')[0]
        
        # Prepare items for the template
        items = []
        for name in file_list:
            # Skip hidden files
            if name.startswith('.'):
                continue
                
            fullname = os.path.join(path, name)
            is_dir = os.path.isdir(fullname)
            
            # Get file info
            if is_dir:
                size = self._get_dir_size(fullname)
                last_modified = os.path.getmtime(fullname)
            else:
                size, last_modified = get_file_info(fullname)
                
            items.append((name, is_dir, size, last_modified))
        
        # Apply sorting
        if sort_by == 'name':
            items.sort(key=lambda x: x[0].lower(), reverse=(sort_order == 'desc'))
        elif sort_by == 'type':
            items.sort(key=lambda x: (not x[1], x[0].lower()), reverse=(sort_order == 'desc'))
        elif sort_by == 'size':
            items.sort(key=lambda x: (x[2], x[0].lower()), reverse=(sort_order == 'desc'))
        elif sort_by == 'modified':
            items.sort(key=lambda x: (x[3], x[0].lower()), reverse=(sort_order == 'desc'))
            
        return items, display_path, sort_by, sort_order
    
    def list_directory(self, path):
        """Override the list_directory method to include the upload form and sorting."""
        items, display_path, sort_by, sort_order = self._prepare_directory_items(path)
        if items is None:
            return None
        
        # Generate HTML content
        html_content = generate_directory_listing(display_path, items, sort_by, sort_order)
        
        # Send the response
        encoded = html_content.encode('utf-8', 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f
    
    def _get_dir_size(self, path):
        """Recursively calculate total size of a directory."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                # Skip hidden files and directories
                filenames = [f for f in filenames if not f.startswith('.')]
                dirnames[:] = [d for d in dirnames if not d.startswith('.')]
                
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
        except (OSError, PermissionError):
            return 0
        return total_size
    
    def do_POST(self):
        """Handle POST requests for file uploads and folder creation."""
        # Check if path is safe
        path = self.translate_path(self.path)
        data_dir = os.path.join(os.getcwd(), self.data_directory)
        
        if not path.startswith(data_dir) or not os.path.isdir(path):
            self.send_error(403, "Forbidden - operations only allowed in data directory")
            return
        
        # Parse the query string to determine the action
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        action = query_components.get('action', ['upload'])[0]
        
        handlers = {
            'upload': self._handle_file_upload,
            'create_folder': self._handle_folder_creation,
            'delete': self._handle_file_deletion
        }
        
        if action in handlers:
            handlers[action](path)
        else:
            self.send_error(400, "Bad request - unknown action")
    
    def _handle_file_upload(self, path):
        """Handle file upload requests."""
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-Type'],
            }
        )
        
        if 'files' not in form:
            self.send_error(400, "Bad request - missing files field")
            return
        
        # Handle both single and multiple file uploads
        file_list = form['files'] if isinstance(form['files'], list) else [form['files']]
        
        # Process each file
        for file_item in file_list:
            if not file_item.filename:
                continue
                
            # Sanitize the filename and create the file path
            filename = os.path.basename(file_item.filename)
            file_path = os.path.join(path, filename)
            
            try:
                with open(file_path, 'wb') as f:
                    f.write(file_item.file.read())
            except Exception as e:
                self.send_error(500, f"Server error: {str(e)}")
                return
        
        # Redirect back to the current directory
        self._redirect_to_directory()
    
    def _redirect_to_directory(self):
        """Redirect back to the current directory."""
        self.send_response(303)
        self.send_header("Location", self.path.split('?')[0])
        self.end_headers()
    
    def _handle_folder_creation(self, path):
        """Handle folder creation requests."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = urllib.parse.parse_qs(post_data)
        
        folder_name = form_data.get('folder_name', [''])[0]
        
        if not folder_name:
            self.send_error(400, "Bad request - missing folder name")
            return
        
        # Sanitize the folder name and create the folder path
        folder_name = os.path.basename(folder_name)
        folder_path = os.path.join(path, folder_name)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            self._redirect_to_directory()
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def _handle_file_deletion(self, path):
        """Handle file/folder deletion requests."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = urllib.parse.parse_qs(post_data)
            
            filename = form_data.get('filename', [''])[0]
            
            if not filename:
                return self._show_directory_with_error(path, "Missing filename")
            
            # Sanitize the filename and create the full path
            filename = os.path.basename(filename.rstrip('/'))
            file_path = os.path.join(path, filename)
            
            # Check if path exists and is within data directory
            data_dir = os.path.join(os.getcwd(), self.data_directory)
            if not os.path.exists(file_path):
                return self._show_directory_with_error(path, "File not found")
            if not os.path.realpath(file_path).startswith(data_dir):
                return self._show_directory_with_error(path, "Cannot delete files outside data directory")
            
            # Delete the file/folder
            if os.path.isdir(file_path):
                if not os.listdir(file_path):  # Check if directory is empty
                    os.rmdir(file_path)
                    self._redirect_to_directory()
                else:
                    return self._show_directory_with_error(path, "Directory not empty - contains files or subdirectories")
            else:
                os.remove(file_path)
                self._redirect_to_directory()
                
        except OSError as e:
            return self._show_directory_with_error(path, f"Failed to delete: {str(e)}")
        except Exception as e:
            return self._show_directory_with_error(path, f"Server error: {str(e)}")

    def _show_directory_with_error(self, path, error_message):
        """Show directory listing with an error message."""
        items, display_path, sort_by, sort_order = self._prepare_directory_items(path)
        if items is None:
            return None
        
        # Generate HTML content with error message
        html_content = generate_directory_listing(
            display_path, items, sort_by, sort_order, 
            error_message=error_message
        )
        
        # Send response
        encoded = html_content.encode('utf-8', 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        
        self.copyfile(f, self.wfile)
        return None

    def do_GET(self):
        """Handle GET requests for files and directories."""
        # Check if this is a request for a static file
        if self.path.startswith('/static/'):
            self.serve_static_file()
            return
        
        # Get the file path
        path = self.translate_path(self.path)
        
        # If it's a directory, show the listing
        if os.path.isdir(path):
            return super().do_GET()
        
        # If it's a file, serve it
        try:
            if not os.path.exists(path):
                self.send_error(404, "File not found")
                return
            
            # Serve the file
            with open(path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, f"Error serving file: {str(e)}")

    def guess_type(self, path):
        """Guess the type of a file based on its extension."""
        ext = os.path.splitext(path)[1].lower()
        return self.extensions_map.get(ext, self.extensions_map[''])

    def translate_static_path(self, path):
        """Translate a static file path to a local file path."""
        # Remove /static/ prefix and get the static directory
        rel_path = path[8:]  # Remove '/static/'
        cwd = os.getcwd()
        static_dir = os.path.join(cwd, 'static')
        
        # Ensure the static directory exists
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
        
        # Join with the relative path and ensure it's within the static directory
        file_path = os.path.normpath(os.path.join(static_dir, rel_path))
        return file_path if file_path.startswith(static_dir) else os.path.join(static_dir, 'index.html')

    def serve_static_file(self):
        """Serve static files from the static directory."""
        file_path = self.translate_static_path(self.path)
        
        try:
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_error(404, "File not found")
                return
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header("Content-type", self.guess_type(file_path))
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
