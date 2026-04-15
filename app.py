from __future__ import annotations

import importlib.util
import os
import re
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
UI_SCRIPT = PROJECT_ROOT / "dissidio_ui.py"
REQUIRED_MODULES = {
    "streamlit": "streamlit",
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "plotly": "plotly",
}


def venv_python() -> Path:
    if sys.platform.startswith("win"):
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def ensure_virtualenv() -> Path:
    python_path = venv_python()
    if python_path.exists():
        return python_path

    print("Criando ambiente virtual local em .venv...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)], cwd=PROJECT_ROOT)
    return python_path


def running_inside_project_venv() -> bool:
    try:
        return Path(sys.executable).resolve() == venv_python().resolve()
    except FileNotFoundError:
        return False


def missing_modules() -> list[str]:
    missing = []
    for module_name in REQUIRED_MODULES:
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    return missing


def install_requirements(python_path: Path) -> None:
    print("Preparando pip no ambiente virtual...")
    subprocess.check_call([str(python_path), "-m", "ensurepip", "--upgrade"], cwd=PROJECT_ROOT)
    subprocess.check_call(
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools",
            "wheel",
            "--disable-pip-version-check",
        ],
        cwd=PROJECT_ROOT,
    )
    subprocess.check_call(
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "-r",
            str(REQUIREMENTS_FILE),
            "--disable-pip-version-check",
        ],
        cwd=PROJECT_ROOT,
    )


def find_free_port(start_port: int = 8501, attempts: int = 50) -> int:
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("Nao foi possivel localizar uma porta livre para iniciar o Streamlit.")


def stream_process_output(process: subprocess.Popen[str]) -> int:
    browser_opened = False
    url_pattern = re.compile(r"https?://[^\s]+")

    if process.stdout is None:
        return process.wait()

    try:
        for raw_line in process.stdout:
            line = raw_line.rstrip("\r\n")
            print(line)

            if not browser_opened:
                match = url_pattern.search(line)
                if match:
                    webbrowser.open(match.group(0), new=2)
                    browser_opened = True
    finally:
        process.stdout.close()

    return process.wait()


def relaunch_inside_venv() -> int:
    python_path = ensure_virtualenv()
    args = [str(python_path), str(Path(__file__).resolve()), *sys.argv[1:]]
    return subprocess.call(args, cwd=PROJECT_ROOT)


def run_streamlit() -> int:
    python_path = Path(sys.executable)
    missing = missing_modules()
    if missing:
        missing_labels = ", ".join(REQUIRED_MODULES[module] for module in missing)
        print(f"Dependencias ausentes detectadas: {missing_labels}")
        print("Instalando bibliotecas necessarias...")
        install_requirements(python_path)

    port = find_free_port()
    url = f"http://localhost:{port}"
    if port != 8501:
        print(f"Porta 8501 ocupada. Usando {port}.")

    command = [
        str(python_path),
        "-m",
        "streamlit",
        "run",
        str(UI_SCRIPT),
        "--server.address",
        "localhost",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    print(f"Iniciando a calculadora em {url}")
    process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    return stream_process_output(process)


def main() -> int:
    if not running_inside_project_venv():
        return relaunch_inside_venv()

    return run_streamlit()


if __name__ == "__main__":
    raise SystemExit(main())
