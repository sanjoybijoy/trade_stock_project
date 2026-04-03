import os
import subprocess
import webbrowser
from threading import Timer

# Absolute path to your Django project (where manage.py is located)
PROJECT_DIR = r"D:\Trading\Django\Trade_analysis\trading_analysis_0_14_local_mysq"
os.chdir(PROJECT_DIR)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8000")

if __name__ == "__main__":
    # Set the default Django settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trading_analysis.settings")
    # Start the server and open the browser
    Timer(1, open_browser).start()
    subprocess.run(["python", "manage.py", "runserver", "127.0.0.1:8000"])
