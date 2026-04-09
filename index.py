import os
import sys

# Add the project subdirectory to the python path
project_path = os.path.join(os.path.dirname(__file__), 'echonotes')
if project_path not in sys.path:
    sys.path.append(project_path)

# Set the settings module (the 'echonotes.settings' corresponds to the inner folder)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')

# Import the application handler
try:
    from echonotes.wsgi import application
    app = application
except ImportError as e:
    print(f"Error importing WSGI application: {e}")
    # Fallback to inner import path if needed
    try:
        from wsgi import application
        app = application
    except ImportError:
         raise e
