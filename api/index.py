import os
import sys

# Add the project subdirectory to the python path
project_path = os.path.join(os.path.dirname(__file__), '..', 'echonotes')
if project_path not in sys.path:
    sys.path.append(project_path)

# Set the settings module (the 'echonotes.settings' corresponds to the inner folder)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')

# Import the application handler
try:
    print(f"DEBUG: Current directory: {os.getcwd()}")
    print(f"DEBUG: sys.path: {sys.path}")
    from echonotes.wsgi import application
    app = application
    print("DEBUG: Successfully imported echonotes.wsgi")
except ImportError as e:
    print(f"DEBUG: Error importing echonotes.wsgi: {e}")
    # Fallback to direct wsgi import if needed
    try:
        from wsgi import application
        app = application
        print("DEBUG: Successfully imported wsgi from fallback")
    except ImportError as inner_e:
         print(f"DEBUG: Final import error: {inner_e}")
         raise e
