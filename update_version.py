import subprocess
import sys

def update_version(version_part):
    try:
        subprocess.run(['bump2version', version_part], check=True)
        print(f"Version updated successfully. New version: {get_current_version()}")
    except subprocess.CalledProcessError as e:
        print(f"Error updating version: {e}")
        sys.exit(1)

def get_current_version():
    with open('__init__.py', 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"')
    return "Unknown"

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['major', 'minor', 'patch']:
        print("Usage: python update_version.py [major|minor|patch]")
        sys.exit(1)
    
    update_version(sys.argv[1])