import os
import subprocess
import sys

def run_command(command):
    """
    Helper to run a shell command and print its output.
    """
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

def main():
    # 1. Define Paths
    base_output_dir = os.path.join("output", "employee_history")
    
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)

    print("--- Step 1: Processing Employee History ---")
    # Run the YTD processor
    run_command([sys.executable, "./payroll/process_employee_ytd.py"])
    print("Employee YTD JSON data generated successfully.\n")

    print("--- Step 2: Generating Employee PDFs ---")
    
    # Define the generation job
    data_file = "data/employee_ytd_reports.json"
    template_name = "employee_ytd_report.html"
    
    cmd = [
        sys.executable, "main.py",
        "--data", data_file,
        "--template", template_name,
        "--out", base_output_dir,
        "--id-key", "document_id"  # Uses the 'document_id' field (e.g., YTD-EMP-12345)
    ]
    
    run_command(cmd)

    print("\n--- Pipeline Complete ---")
    print(f"Employee YTD Reports have been output to: {base_output_dir}")

if __name__ == "__main__":
    main()