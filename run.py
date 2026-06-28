#!/usr/bin/env python
"""
MRI AI Tumor Detection System - Single Launcher
Starts Backend, Frontend, and AI Service with one command.
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_banner():
    print(f"""
{BOLD}{BLUE}╔═══════════════════════════════════════════════════════════════╗
║     MRI AI Tumor & Anomaly Detection System                ║
║     Starting All Services...                               ║
╚═══════════════════════════════════════════════════════════════╝{RESET}
    """)

def run_command(cmd, cwd, name, color):
    """Run a command in a separate thread and print output."""
    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"{color}[{name}]{RESET} Started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"{YELLOW}[{name}]{RESET} Error: {e}")
        return None

def main():
    base_dir = Path(__file__).parent.resolve()
    
    print_banner()
    
    processes = []
    
    # 1. Backend
    print(f"{GREEN}[1/3]{RESET} Starting Backend (port 8000)...")
    backend_cmd = r"..\.venv\Scripts\Activate && uvicorn app.main:app --reload --port 8000"
    backend_process = subprocess.Popen(
        f"cmd /k \"cd /d \"{base_dir}\\backend\" && {backend_cmd}\"",
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    processes.append(("Backend", backend_process))
    time.sleep(2)
    
    # 2. Frontend
    print(f"{GREEN}[2/3]{RESET} Starting Frontend (port 5173)...")
    frontend_cmd = "npm run dev"
    frontend_process = subprocess.Popen(
        f"cmd /k \"cd /d \"{base_dir}\\frontend\" && {frontend_cmd}\"",
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    processes.append(("Frontend", frontend_process))
    time.sleep(2)
    
    # 3. AI Service
    print(f"{GREEN}[3/3]{RESET} Starting AI Service (port 8001)...")
    ai_cmd = r"..\.venv\Scripts\Activate && python service.py"
    ai_process = subprocess.Popen(
        f"cmd /k \"cd /d \"{base_dir}\\ai\" && {ai_cmd}\"",
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    processes.append(("AI Service", ai_process))
    
    print(f"""
{BOLD}{GREEN}═══════════════════════════════════════════════════════════════
   All Services Started Successfully!
═══════════════════════════════════════════════════════════════{RESET}

   📍 Backend API:    http://localhost:8000
   🌐 Frontend UI:   http://localhost:5173  
   🤖 AI Service:    http://localhost:8001

   {YELLOW}Open http://localhost:5173 in your browser to use the system{RESET}

   {YELLOW}Press Ctrl+C in any terminal to stop that service{RESET}
""")
    
    # Keep running until user presses Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nStopping all services...")
        for name, proc in processes:
            try:
                proc.terminate()
                print(f"Stopped {name}")
            except:
                pass

if __name__ == "__main__":
    main()