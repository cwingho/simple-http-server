import os
import re
import html
import urllib.parse
from datetime import datetime

def format_size(size):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def format_date(timestamp):
    """Format timestamp as a readable date."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def load_template(template_name):
    """
    Load a template file from the templates directory.
    
    Args:
        template_name (str): Name of the template file
        
    Returns:
        str: Content of the template file
    """
    # Get the current directory
    cwd = os.getcwd()
    
    # Join with the templates directory
    templates_dir = os.path.join(cwd, 'templates')
    
    # Ensure the templates directory exists
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir, exist_ok=True)
    
    # Join with the template name
    template_path = os.path.join(templates_dir, template_name)
    
    # Read the template
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def render_template(template_name, **context):
    """
    Render a template with the given context.
    
    Args:
        template_name (str): Name of the template file
        **context: Variables to pass to the template
        
    Returns:
        str: Rendered template
    """
    # Load the template
    template = load_template(template_name)
    
    # Replace variables in the template
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        template = template.replace(placeholder, str(value))
    
    # Handle conditional blocks
    template = process_conditionals(template, context)
    
    # Handle loops
    template = process_loops(template, context)
    
    return template

def process_conditionals(template, context):
    """Process conditional blocks in the template."""
    # Find all conditional blocks
    pattern = r'{%\s*if\s+(\w+)\s*%}(.*?){%\s*endif\s*%}'
    
    def replace_conditional(match):
        condition_var = match.group(1)
        content = match.group(2)
        
        # Check if the condition is true
        if condition_var in context and context[condition_var]:
            return content
        return ''
    
    # Replace all conditional blocks
    return re.sub(pattern, replace_conditional, template, flags=re.DOTALL)

def process_loops(template, context):
    """Process loop blocks in the template."""
    # Find all loop blocks
    pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}'
    
    def replace_loop(match):
        item_var = match.group(1)
        collection_var = match.group(2)
        content = match.group(3)
        
        # Check if the collection exists
        if collection_var not in context or not context[collection_var]:
            return ''
        
        # Process each item in the collection
        result = []
        for item in context[collection_var]:
            # Create a copy of the context with the item variable
            item_context = context.copy()
            item_context[item_var] = item
            
            # Replace variables in the content
            item_content = content
            
            # Handle item attributes
            for attr_name, attr_value in item.items() if isinstance(item, dict) else []:
                placeholder = f"{{{{{item_var}.{attr_name}}}}}"
                item_content = item_content.replace(placeholder, str(attr_value))
            
            result.append(item_content)
        
        return ''.join(result)
    
    # Replace all loop blocks
    return re.sub(pattern, replace_loop, template, flags=re.DOTALL)

def generate_directory_listing(display_path, items, sort_by='name', sort_order='asc', error_message=None):
    """
    Generate HTML for directory listing using templates.
    
    Args:
        directory_path (str): Actual path to the directory
        display_path (str): Path to display in the HTML
        items (list): List of (name, is_dir, size, last_modified) tuples
        sort_by (str): Column to sort by ('name', 'type', 'size', 'modified')
        sort_order (str): Sort order ('asc' or 'desc')
        error_message (str, optional): Error message to display
        
    Returns:
        str: HTML content for the directory listing page
    """
    # Escape the display path for HTML
    display_path = html.escape(display_path)
    
    # Create sort links
    def get_sort_link(column):
        new_order = 'desc' if sort_by == column and sort_order == 'asc' else 'asc'
        arrow = ''
        if sort_by == column:
            arrow = ' ▲' if sort_order == 'asc' else ' ▼'
        return f"?sort={column}&order={new_order}", arrow
    
    name_link, name_arrow = get_sort_link('name')
    type_link, type_arrow = get_sort_link('type')
    size_link, size_arrow = get_sort_link('size')
    modified_link, modified_arrow = get_sort_link('modified')
    
    # Prepare items for the template
    file_items = []
    show_parent = display_path != '/'
    
    # Add each item in the directory
    for name, is_dir, size, last_modified in items:
        # Escape the name for HTML and URL
        escaped_name = html.escape(name)
        urlencoded_name = urllib.parse.quote(name)
        
        # Format the size and date
        size_str = '-' if is_dir else format_size(size)
        date_str = format_date(last_modified)
        
        # Add trailing slash for directories in display
        display_name = escaped_name + ('/' if is_dir else '')
        
        # Add icon based on file type
        icon = "📁" if is_dir else "📄"
        
        file_items.append({
            'name': display_name,
            'url': f"{urlencoded_name}{'/' if is_dir else ''}",
            'icon': icon,
            'is_dir': is_dir,
            'type': 'Directory' if is_dir else 'File',
            'size': size,
            'size_str': size_str,
            'date': date_str
        })
    
    # Render the template
    return render_template('directory.html', 
                          display_path=display_path,
                          name_link=name_link,
                          name_arrow=name_arrow,
                          type_link=type_link,
                          type_arrow=type_arrow,
                          size_link=size_link,
                          size_arrow=size_arrow,
                          modified_link=modified_link,
                          modified_arrow=modified_arrow,
                          show_parent=show_parent,
                          items=file_items,
                          error_message=error_message) 