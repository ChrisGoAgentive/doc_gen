import sys
import os
import subprocess

# Simple orchestrator to run the I-9 generation
# This separates the I-9 process from the withdrawals pipeline

def run_command(command):
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    print("--- Starting I-9 Compliance Pipeline ---")
    
    # Define paths relative to the project root
    script_path = os.path.join("i9", "generate_i9.py")
    data_path = os.path.join("data", "hr_employee_file_rich.json")
    
    # Command to run the generator
    cmd = [
        sys.executable, script_path,
        "--data", data_path,
        "--out", os.path.join("output", "i9_forms")
    ]
    
    run_command(cmd)
    
    print("--- I-9 Pipeline Finished Successfully ---")

if __name__ == "__main__":
    main()