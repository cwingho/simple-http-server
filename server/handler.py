import os
import io
import cgi
import urllib.parse
from http.server import SimpleHTTPRequestHandler

from server.path_utils import normalize_path, is_path_safe, get_file_info
from server.template_loader import generate_directory_listing

class UploadEnabledHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with file upload capability that restricts access to ./data/."""
    
    # Define the data directory
    data_directory = "data"
    
    def translate_path(self, path):
        """
        Override translate_path to restrict access to the data directory.
        """
        # First normalize the URL path
        path = path.split('?', 1)[0]  # Remove query parameters
        path = path.split('#', 1)[0]  # Remove fragment
        
        # Decode percent-encoded characters
        path = urllib.parse.unquote(path)
        
        # Convert to native OS path format
        path = path.replace('/', os.sep)
        
        # Make it absolute
        cwd = os.getcwd()
        data_dir = os.path.join(cwd, self.data_directory)
        
        # Ensure data directory exists
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        # If it's the root path, return data directory
        if not path or path == '/':
            return data_dir
        
        # Remove any leading separator
        while path.startswith(os.sep):
            path = path[1:]
        
        # Join with data directory and normalize
        full_path = os.path.normpath(os.path.join(data_dir, path))
        
        # Ensure the path is still within data directory
        if not full_path.startswith(data_dir):
            return data_dir
        
        return full_path
    
    def list_directory(self, path):
        """
        Override the list_directory method to include the upload form and sorting.
        """
        try:
            # Get list of directory contents
            file_list = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None
        
        # Get query parameters for sorting
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        sort_by = query_components.get('sort', ['name'])[0]
        sort_order = query_components.get('order', ['asc'])[0]
        
        # Sort entries
        file_list.sort(key=lambda a: a.lower())
        
        # Get display path
        display_path = urllib.parse.unquote(self.path)
        # Remove query parameters from display path
        display_path = display_path.split('?')[0]
        
        # Prepare items for the template
        items = []
        for name in file_list:
            fullname = os.path.join(path, name)
            
            # Skip hidden files
            if name.startswith('.'):
                continue
                
            # Get file info
            is_dir = os.path.isdir(fullname)
            
            if is_dir:
                size, last_modified = 0, os.path.getmtime(fullname)
            else:
                size, last_modified = get_file_info(fullname)
                
            items.append((name, is_dir, size, last_modified))
        
        # Apply sorting based on sort_by and sort_order
        if sort_by == 'name':
            items.sort(key=lambda x: x[0].lower(), reverse=(sort_order == 'desc'))
        elif sort_by == 'type':
            items.sort(key=lambda x: (not x[1], x[0].lower()), reverse=(sort_order == 'desc'))
        elif sort_by == 'size':
            items.sort(key=lambda x: (x[2], x[0].lower()), reverse=(sort_order == 'desc'))
        elif sort_by == 'modified':
            items.sort(key=lambda x: (x[3], x[0].lower()), reverse=(sort_order == 'desc'))
        
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
    
    def do_POST(self):
        """Handle POST requests for file uploads and folder creation."""
        # Check if path is safe
        path = self.translate_path(self.path)
        data_dir = os.path.join(os.getcwd(), self.data_directory)
        
        if not path.startswith(data_dir):
            self.send_error(403, "Forbidden - operations only allowed in data directory")
            return
            
        # Check if the path is a directory
        if not os.path.isdir(path):
            self.send_error(405, "Method not allowed")
            return
        
        # Parse the query string to determine the action
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        action = query_components.get('action', ['upload'])[0]
        
        if action == 'upload':
            self._handle_file_upload(path)
        elif action == 'create_folder':
            self._handle_folder_creation(path)
        elif action == 'delete':
            self._handle_file_deletion(path)
        else:
            self.send_error(400, "Bad request - unknown action")
    
    def _handle_file_upload(self, path):
        """Handle file upload requests."""
        # Parse the form data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-Type'],
            }
        )
        
        # Check if the files field is in the form
        if 'files' not in form:
            self.send_error(400, "Bad request - missing files field")
            return
        
        # Get the file items (could be multiple)
        file_items = form['files']
        
        # Handle both single and multiple file uploads
        if isinstance(file_items, list):
            # Multiple files
            file_list = file_items
        else:
            # Single file
            file_list = [file_items]
        
        # Process each file
        uploaded_files = []
        for file_item in file_list:
            # Check if a file was actually uploaded
            if not file_item.filename:
                continue
                
            # Sanitize the filename
            filename = os.path.basename(file_item.filename)
            
            # Create the file path
            file_path = os.path.join(path, filename)
            
            try:
                # Write the file
                with open(file_path, 'wb') as f:
                    f.write(file_item.file.read())
                uploaded_files.append(filename)
            except Exception as e:
                self.send_error(500, f"Server error: {str(e)}")
                return
        
        # Redirect back to the current directory
        self.send_response(303)
        self.send_header("Location", self.path.split('?')[0])
        self.end_headers()
    
    def _handle_folder_creation(self, path):
        """Handle folder creation requests."""
        # Get the content length
        content_length = int(self.headers['Content-Length'])
        
        # Read the POST data
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse the form data
        form_data = urllib.parse.parse_qs(post_data)
        
        # Get the folder name
        folder_name = form_data.get('folder_name', [''])[0]
        
        if not folder_name:
            self.send_error(400, "Bad request - missing folder name")
            return
        
        # Sanitize the folder name (remove path separators)
        folder_name = os.path.basename(folder_name)
        
        # Create the folder path
        folder_path = os.path.join(path, folder_name)
        
        try:
            # Create the folder
            os.makedirs(folder_path, exist_ok=True)
            
            # Redirect back to the current directory
            self.send_response(303)
            self.send_header("Location", self.path.split('?')[0])
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def _handle_file_deletion(self, path):
        """Handle file/folder deletion requests."""
        try:
            # Get the content length
            content_length = int(self.headers['Content-Length'])
            
            # Read the POST data
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parse the form data
            form_data = urllib.parse.parse_qs(post_data)
            
            # Get the filename
            filename = form_data.get('filename', [''])[0]
            
            if not filename:
                f = self._show_directory_with_error(path, "Missing filename")
                if f:
                    self.copyfile(f, self.wfile)
                return
            
            # Remove trailing slash if present (important for directories)
            filename = filename.rstrip('/')
            
            # Sanitize the filename
            filename = os.path.basename(filename)
            
            # Create the full path
            file_path = os.path.join(path, filename)
            
            # Check if path exists
            if not os.path.exists(file_path):
                f = self._show_directory_with_error(path, "File not found")
                if f:
                    self.copyfile(f, self.wfile)
                return
            
            # Check if path is within data directory
            data_dir = os.path.join(os.getcwd(), self.data_directory)
            if not os.path.realpath(file_path).startswith(data_dir):
                f = self._show_directory_with_error(path, "Cannot delete files outside data directory")
                if f:
                    self.copyfile(f, self.wfile)
                return
            
            # Delete the file/folder
            if os.path.isdir(file_path):
                try:
                    # First check if directory is actually empty
                    if not os.listdir(file_path):
                        os.rmdir(file_path)
                        # Redirect back to the current directory
                        self.send_response(303)
                        self.send_header("Location", self.path.split('?')[0])
                        self.end_headers()
                    else:
                        f = self._show_directory_with_error(path, "Directory not empty - contains files or subdirectories")
                        if f:
                            self.copyfile(f, self.wfile)
                except OSError as e:
                    f = self._show_directory_with_error(path, f"Failed to delete directory: {str(e)}")
                    if f:
                        self.copyfile(f, self.wfile)
            else:
                try:
                    os.remove(file_path)
                    # Redirect back to the current directory
                    self.send_response(303)
                    self.send_header("Location", self.path.split('?')[0])
                    self.end_headers()
                except OSError as e:
                    f = self._show_directory_with_error(path, f"Failed to delete file: {str(e)}")
                    if f:
                        self.copyfile(f, self.wfile)
        
        except Exception as e:
            f = self._show_directory_with_error(path, f"Server error: {str(e)}")
            if f:
                self.copyfile(f, self.wfile)

    def _show_directory_with_error(self, path, error_message):
        """Show directory listing with an error message."""
        try:
            # Get list of directory contents
            file_list = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None
        
        # Get query parameters for sorting
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        sort_by = query_components.get('sort', ['name'])[0]
        sort_order = query_components.get('order', ['asc'])[0]
        
        # Get display path
        display_path = urllib.parse.unquote(self.path)
        display_path = display_path.split('?')[0]
        
        # Prepare items for the template
        items = []
        for name in file_list:
            fullname = os.path.join(path, name)
            
            # Skip hidden files
            if name.startswith('.'):
                continue
                
            # Get file info
            is_dir = os.path.isdir(fullname)
            
            if is_dir:
                size, last_modified = 0, os.path.getmtime(fullname)
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
        return f

    def do_GET(self):
        """Handle GET requests for files and directories."""
        # Check if this is a request for a static file
        if self.path.startswith('/static/'):
            self.serve_static_file()
            return
        
        # Otherwise, handle normally
        return super().do_GET()

    def serve_static_file(self):
        """Serve static files from the static directory."""
        # Get the file path
        file_path = self.translate_static_path(self.path)
        
        try:
            # Check if file exists
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_error(404, "File not found")
                return
            
            # Determine content type
            content_type = self.get_content_type(file_path)
            
            # Open the file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Send response
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def translate_static_path(self, path):
        """Translate a static file path to a local file path."""
        # Remove /static/ prefix
        rel_path = path[8:]  # Remove '/static/'
        
        # Get the current directory
        cwd = os.getcwd()
        
        # Join with the static directory
        static_dir = os.path.join(cwd, 'static')
        
        # Ensure the static directory exists
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
        
        # Join with the relative path
        file_path = os.path.normpath(os.path.join(static_dir, rel_path))
        
        # Ensure the path is still within the static directory
        if not file_path.startswith(static_dir):
            return os.path.join(static_dir, 'index.html')
        
        return file_path

    def get_content_type(self, path):
        """Get the content type based on file extension."""
        ext = os.path.splitext(path)[1].lower()
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
        }
        return content_types.get(ext, 'application/octet-stream') 