"""
Utility script to create a clean, portable distribution zip for transfer.
Excludes node_modules, dev venv, and git files to keep the archive compact.
"""
import os
import zipfile
import shutil
from datetime import datetime

def pack():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(root_dir, "LocalLogistic_Portable.zip")
    
    print(f"Формирование портативного архива для отправки: {output_filename}...")
    
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

    excluded_dirs = {"venv", "node_modules", ".git", "__pycache__", ".pytest_cache"}
    excluded_extensions = {".pyc", ".log", ".tmp"}

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for rel_path in include_paths:
            full_path = os.path.join(root_dir, rel_path)
            if not os.path.exists(full_path):
                print(f"Пропуск (не найден): {rel_path}")
                continue

            if os.path.isfile(full_path):
                zipf.write(full_path, arcname=rel_path)
                print(f"Добавлен файл: {rel_path}")
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
                print(f"Добавлена папка: {rel_path}")

    size_mb = os.path.getsize(output_filename) / (1024 * 1024)
    print("=" * 60)
    print(f"ГОТОВО! Архив успешно создан: LocalLogistic_Portable.zip")
    print(f"Размер архива: {size_mb:.1f} МБ")
    print("Маме достаточно распаковать архив и запустить: Запустить_Транспорт.bat")
    print("=" * 60)

if __name__ == "__main__":
    pack()
