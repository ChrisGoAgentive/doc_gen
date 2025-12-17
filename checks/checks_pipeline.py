import os
import subprocess
import sys

def run_command(command):
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

def main():
    # 1. Define Paths
    # Ensure we operate from project root context if possible
    # checks/process_checks.py generates data/checks.json
    
    print("--- Step 1: Processing Check Data ---")
    run_command([sys.executable, "checks/process_checks.py"])
    
    print("\n--- Step 2: Generating Check PDFs ---")
    data_file = "data/checks.json"
    output_dir = "output/checks"
    
    cmd = [
        sys.executable, "checks/generate_checks.py",
        "--data", data_file,
        "--out", output_dir
    ]
    
    run_command(cmd)

    print("\n--- Check Pipeline Complete ---")
    print(f"Checks generated in: {output_dir}")

if __name__ == "__main__":
    main()