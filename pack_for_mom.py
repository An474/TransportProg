"""
Utility script to create a clean, portable distribution zip for transfer.
Automatically builds frontend if npm is available, and packs the bundle.
"""
import os
import sys
import subprocess
import zipfile
import shutil

def run_frontend_build(root_dir):
    frontend_dir = os.path.join(root_dir, "frontend")
    if os.path.exists(os.path.join(frontend_dir, "package.json")):
        print("[1/2] Сборка интерфейса (npm run build)...")
        try:
            res = subprocess.run("cmd /c npm run build", shell=True, cwd=frontend_dir)
            if res.returncode == 0:
                print("  -> Сборка интерфейса успешно завершена.")
            else:
                print("  -> Внимание: сборка интерфейса завершилась с кодом", res.returncode)
        except Exception as e:
            print("  -> Пропуск npm build (не удалось запустить):", str(e))
    else:
        print("[1/2] Папка frontend не найдена, используется существующий dist.")

def pack():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(root_dir, "LocalLogistic_Portable.zip")
    
    print("=" * 65)
    print("   ФОРМИРОВАНИЕ ПОРТАТИВНОГО АРХИВА ДЛЯ ОТПРАВКИ")
    print("=" * 65)

    # 1. Build frontend
    run_frontend_build(root_dir)

    print("\n[2/2] Упаковка портативного дистрибутива в zip...")
    
    # Folders and files to include
    include_paths = [
        "python_runtime",
        "backend/app",
        "backend/data",
        "frontend/dist",
        "run.py",
        "start_local.bat",
        "START.bat",
        "Запустить_Транспорт.bat",
        "README.md",
    ]

    excluded_dirs = {"venv", "node_modules", ".git", "__pycache__", ".pytest_cache", "updates"}
    excluded_extensions = {".pyc", ".log", ".tmp"}

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for rel_path in include_paths:
            full_path = os.path.join(root_dir, rel_path)
            if not os.path.exists(full_path):
                print(f"  Пропуск (не найден): {rel_path}")
                continue

            if os.path.isfile(full_path):
                zipf.write(full_path, arcname=rel_path)
                print(f"  + Файл: {rel_path}")
            elif os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    # Filter out excluded directories
                    dirs[:] = [d for d in dirs if d not in excluded_dirs]
                    
                    for f in files:
                        _, ext = os.path.splitext(f)
                        if ext in excluded_extensions:
                            continue
                        file_full = os.path.join(root, f)
                        file_rel = os.path.relpath(file_full, root_dir)
                        zipf.write(file_full, arcname=file_rel)
                print(f"  + Папка: {rel_path}")

    size_mb = os.path.getsize(output_filename) / (1024 * 1024)
    print("=" * 65)
    print("  ГОТОВО! Архив успешно создан:")
    print(f"  Файл:   {output_filename}")
    print(f"  Размер: {size_mb:.1f} МБ")
    print("=" * 65)
    print("  Этот файл можно отправлять маме на флешке или через мессенджер.")
    print("=" * 65)

if __name__ == "__main__":
    pack()
