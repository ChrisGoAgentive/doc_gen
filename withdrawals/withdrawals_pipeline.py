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
    # We output to a distinct folder for 401k documents
    base_output_dir = os.path.join("output", "401k_withdrawals")
    
    # Ensure the base output directory exists
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)

    print("--- Step 1: Generating JSON Data from HR Records ---")
    # Calls the processing script we designed in the previous step
    # Assumes this pipeline is run from the project root
    run_command([sys.executable, "./withdrawals/process_withdrawals.py"])
    print("JSON data generated successfully.\n")

    print("--- Step 2: Generating PDF Documents from Templates ---")
    
    # 3. Define the batch jobs
    # Format: (Source JSON, Template Name, Output Subfolder Name)
    jobs = [
        # 401k Financial Documents
        ("data/401k_withdrawal.json", "401k_statement_template.html", "statements"),
        ("data/401k_withdrawal.json", "401k_withdrawal_template.html", "withdrawal_forms"),
        
        # HR Notification Letters (All going to "hr notifications" folder)
        ("data/resignations.json", "resignation_template.html", "hr notifications"),
        ("data/separations.json", "separation_template.html", "hr notifications"),
        ("data/death_notifications.json", "death_notification_template.html", "hr notifications")
    ]

    # 4. Run main.py for each job
    for data_file, template_name, subfolder in jobs:
        # Check if the source file exists first. 
        # The process script might not generate a death_notification.json if no deaths occurred.
        if not os.path.exists(data_file):
            print(f"Skipping job for {template_name}: Source file '{data_file}' not found (no records generated).")
            continue

        # Construct the specific output directory (e.g., output/401k_withdrawals/hr notifications)
        job_output_dir = os.path.join(base_output_dir, subfolder)
        
        cmd = [
            sys.executable, "main.py",
            "--data", data_file,
            "--template", template_name,
            "--out", job_output_dir,
            # We use the 'document_id' key which we set to something like "401K-EMP-123"
            "--id-key", "document_id" 
        ]
        run_command(cmd)

    print("\n--- Step 3: Generating 1099-R Tax Forms (PDF Fill) ---")
    
    # Define output directory nested within the withdrawals folder
    f1099_output_dir = os.path.join(base_output_dir, "1099r_forms")
    
    # Execute the 1099 generator script
    cmd_1099 = [
        sys.executable, "withdrawals/generate_1099r.py",
        "--out", f1099_output_dir
    ]
    run_command(cmd_1099)

    print("\n--- Step 4: Generating I-9 Employment Forms (PDF Fill) ---")
    
    # Define output directory nested within the withdrawals folder
    i9_output_dir = os.path.join(base_output_dir, "i9_forms")
    
    # Execute the I-9 generator script
    cmd_i9 = [
        sys.executable, "withdrawals/generate_i9.py",
        "--out", i9_output_dir
    ]
    run_command(cmd_i9)

    print("\n--- Pipeline Complete ---")
    print(f"All 401(k) documents (including 1099-Rs) have been output to: {base_output_dir}")

if __name__ == "__main__":
    main()