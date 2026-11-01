"""
Release builder for Transport Department System.
Builds the frontend and packs update.zip for publishing on GitHub Releases:
https://github.com/An474/TransportProg
"""
import os
import sys
import re
import shutil
import zipfile
import subprocess

def run(cmd, cwd=None):
    print(f">> {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    if res.returncode != 0:
        print(f"ERROR: Command failed with code {res.returncode}: {cmd}")
        sys.exit(1)

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    # 1. Ask or get version
    if len(sys.argv) > 1:
        new_version = sys.argv[1].lstrip("vV")
    else:
        new_version = input("Введите номер новой версии (например, 1.0.1): ").strip().lstrip("vV")

    if not new_version:
        print("Версия не указана. Выход.")
        return

    print("=" * 60)
    print(f"СБОРКА ОБНОВЛЕНИЯ v{new_version}")
    print("=" * 60)

    # 2. Update APP_VERSION in backend/app/core/config.py
    config_path = os.path.join(root_dir, "backend", "app", "core", "config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        conf_content = f.read()

    conf_content = re.sub(
        r'APP_VERSION:\s*str\s*=\s*["\'][^"\']+["\']',
        f'APP_VERSION: str = "{new_version}"',
        conf_content
    )
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(conf_content)
    print(f"[1/4] Версия в backend/app/core/config.py обновлена на: {new_version}")

    # 3. Build frontend
    print("[2/4] Сборка интерфейса (npm run build)...")
    run("cmd /c npm run build", cwd=os.path.join(root_dir, "frontend"))

    # 4. Pack update.zip
    output_zip = os.path.join(root_dir, "update.zip")
    if os.path.exists(output_zip):
        os.remove(output_zip)

    print("[3/4] Упаковка файлов в update.zip...")
    excluded_dirs = {"__pycache__", ".pytest_cache", ".git"}
    excluded_exts = {".pyc", ".tmp", ".log"}

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        # Include VERSION file
        zipf.writestr("VERSION", new_version)

        # Include backend/app
        app_dir = os.path.join(root_dir, "backend", "app")
        for root, dirs, files in os.walk(app_dir):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for f in files:
                _, ext = os.path.splitext(f)
                if ext in excluded_exts:
                    continue
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, root_dir)
                zipf.write(fp, arcname=rel)

        # Include frontend/dist
        dist_dir = os.path.join(root_dir, "frontend", "dist")
        for root, dirs, files in os.walk(dist_dir):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for f in files:
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, root_dir)
                zipf.write(fp, arcname=rel)

    size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"[4/4] Файл update.zip успешно создан! Размер: {size_mb:.2f} МБ")
    print("=" * 60)
    print(f"КАК ОПУБЛИКОВАТЬ РЕЛИЗ НА GITHUB:")
    print(f"1. Откройте страницу релизов:")
    print(f"   https://github.com/An474/TransportProg/releases/new")
    print(f"2. Укажите тег (Choose a tag): v{new_version}")
    print(f"3. Укажите название: Релиз v{new_version}")
    print(f"4. Перетащите в поле 'Attach binaries' файл: update.zip (из корня проекта)")
    print(f"5. Нажмите зеленую кнопку 'Publish release'.")
    print("=" * 60)
    print("После этого у мамы в программе загорится кнопка 'Обновить до v" + new_version + "'!")
    print("=" * 60)

if __name__ == "__main__":
    main()
