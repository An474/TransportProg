import os
import sys
import socket
import threading
import time
import webbrowser
import uvicorn

def get_lan_ip():
    """Gets the primary local network IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def open_browser():
    """Opens browser after server has started."""
    time.sleep(1.5)
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")

    # Change working directory to backend so relative paths work properly
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)

    lan_ip = get_lan_ip()

    print("=" * 73)
    print("      ИНФОРМАЦИОННАЯ СИСТЕМА ТРАНСПОРТНОГО ОТДЕЛА")
    print("=" * 73)
    print()
    print("  [1] Локальный доступ на этом компьютере:")
    print("      http://localhost:8000")
    print()
    print("  [2] Ссылка для коллег отдела в локальной сети компании:")
    print(f"      http://{lan_ip}:8000")
    print("=" * 73)
    print("  Сервер запущен. Открытие браузера...")
    print("  Для остановки программы закройте это окно или нажмите Ctrl + C.")
    print()

    # Launch browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start uvicorn server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
