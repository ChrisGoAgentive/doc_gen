import os
import subprocess
import sys

def run_command(command):
    """
    Helper to run a shell command and print its output.
    Exits the script if the command fails.
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
    base_output_dir = os.path.join("output", "payroll")
    
    # Ensure the output directory exists
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)

    print("--- Step 1: Processing Payroll Journal ---")
    # This assumes payroll/process_payroll.py exists and reads from data/payroll_journal.json
    run_command([sys.executable, "./payroll/process_payroll.py"])
    print("Payroll registers JSON generated successfully.\n")

    print("--- Step 2: Generating Register PDFs ---")
    
    # Define the generation job
    data_file = "data/payroll_registers.json"
    template_name = "payroll_register.html"
    
    cmd = [
        sys.executable, "main.py",
        "--data", data_file,
        "--template", template_name,
        "--out", base_output_dir,
        "--id-key", "document_id"  # Uses the 'document_id' field we created (e.g., REG-PP-20240101)
    ]
    
    run_command(cmd)

    print("\n--- Pipeline Complete ---")
    print(f"Payroll Registers have been output to: {base_output_dir}")

if __name__ == "__main__":
    main()