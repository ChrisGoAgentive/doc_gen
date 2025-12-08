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
    base_output_dir = os.path.join("output", "expenses")
    
    # Ensure the base output directory exists
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
        print(f"Created directory: {base_output_dir}")
    else:
        print(f"Directory exists: {base_output_dir}")

    print("--- Step 1: Generating JSON Data from Ledger ---")
    # 2. Run process_expenses.py to refresh the JSON data in /data
    # We use sys.executable to ensure we use the same python interpreter
    run_command([sys.executable, "./expenses/process_expenses.py"])
    print("JSON data generated successfully.\n")

    print("--- Step 2: Generating Documents ---")
    
    # 3. Define the batch jobs
    # Format: (Source JSON, Template File, Output Folder Name)
    jobs = [
        ("data/invoices.json", "invoice.html", "invoices"),
        ("data/purchase_orders.json", "purchase_order.html", "purchase_orders"),
        ("data/receiving_reports.json", "receiving_report.html", "receiving_reports")
    ]

    # 4. Run main.py for each job
    for data_file, template_file, subfolder in jobs:
        # Construct the specific output directory for this doc type
        # e.g. output/expenses/invoices
        job_output_dir = os.path.join(base_output_dir, subfolder)
        
        cmd = [
            sys.executable, "main.py",
            "--data", data_file,
            "--template", template_file,
            "--out", job_output_dir,
            "--pdf"  # Remove this flag if you only want HTML
        ]
        run_command(cmd)

    print("\n--- Pipeline Complete ---")
    print(f"All documents and data have been output to: {base_output_dir}")

if __name__ == "__main__":
    main()