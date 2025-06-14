import subprocess
import json
import os
from datetime import datetime
import pytz

def run_automation():
    """
    AIM:
    - Automate the segmentation and export workflow for pelvic structures using Mimics and 3-Matic.
    - Generate all necessary parameter files (.json) and execute both software applications sequentially.

    INPUTS:
    - None directly (paths and parameters are defined inside the function but can be adapted).
    - Generates four JSON files:
        * params_mimics.json
        * params_mimics_details.json
        * params_3matic.json
        * params_3matic_details.json

    OUTPUTS:
    - Executes Mimics with a specified script and waits for it to finish.
    - Then executes 3-Matic with a specified script and waits for completion.
    - The actual outputs (e.g., STL files, meshes) are generated by the respective scripts using the JSON parameters.
    """
    
    # 1- GENERAL PARAMETERSz
    subject = "Subject"
    numero = "11"
    
    #Crate the date string
    gmt_tz=pytz.timezone("GMT")
    now=datetime.now(gmt_tz)
    today = now.strftime("%A,%B %d, %Y at %H:%M:%S %Z%z")
    
    # Define the subdirectory path in the current working directory
    subdirectory = os.path.join(os.getcwd(), f"{subject}_{numero}")
    subdirectory_2 = os.path.join(os.getcwd(), f"{subject}_{numero}/{subject}_{numero}")

    # Create the subdirectory if it does not exist
    if not os.path.exists(subdirectory):
        os.makedirs(subdirectory)

    params_mimics = {
        "date":today,
        "subject": subject,
        "numero": numero,
        "dicom_dir": r"E:\IMAGES",
        "export_dir": subdirectory
    }
    with open(os.path.join(subdirectory, "params_mimics.json"), "w") as f:
        json.dump(params_mimics, f)

    params_3matic = {
        "date":today,
        "subject": subject,
        "numero": numero, 
        "stl_l": os.path.join(subdirectory_2, "pelvis_left.stl"),
        "stl_r" : os.path.join(subdirectory_2, "pelvis_right.stl"),
        "export_dir": subdirectory
    }
    with open(os.path.join(subdirectory, "params_3matic.json"), "w") as f:
        json.dump(params_3matic, f)

    # 2- TECHNICAL PARAMETERS
    params_mimics_details = {
        "date":today,
        "subject": subject,
        "numero": numero,
        "threshold_min": 1275,
        "threshold_max": 3524,
        "hole_closing_distance_1": 1,
        "hole_closing_distance_2": 2,
        "wrap_smallest_detail": 0.5,
        "wrap_gap_closing_distance": 5,
        "smooth_factor": 1,
        "smooth_iterations": 20
    }
    with open(os.path.join(subdirectory, "params_mimics_details.json"), "w") as f:
        json.dump(params_mimics_details, f, indent=4)

    params_3matic_details = {
        "date":today,
        "subject": subject,
        "numero": numero, 
        "target_edge_length": 1.3,
        "element_type": "Tet4",
        "volume_max_edge_length": 1.5
    }
    with open(os.path.join(subdirectory, "params_3matic_details.json"), "w") as f:
        json.dump(params_3matic_details, f, indent=4)

    print("Launching Mimics processing...")


    # 3- RUN SCRIPTS
    # Launch Mimics
    mimics_executable = r"C:/Program Files/Materialise/Mimics 26.0/Mimics.exe"
    mimics_script = r"mimics.py"
    mimics_process = subprocess.Popen([mimics_executable, "--r", mimics_script])

    mimics_process.wait()

    print("Launching 3-Matic processing...")

    three_matic_executable = r"C:/Program Files/Materialise/3-matic 18.0 (x64)/3-matic.exe"
    three_matic_script = r"matic.py"

    # Launch 3-matic
    three_matic_process = subprocess.Popen([three_matic_executable, "-run_script", three_matic_script])
    three_matic_process.wait()

    print("All tasks completed.")

if __name__ == "__main__":
    run_automation()
