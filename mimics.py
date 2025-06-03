import os
import json
import re
import tkinter as tk
import tkinter as tk

def wait_for_user_action(split=False, fill=False, title="User Action"):
    """
    Display a custom Tkinter window asking the user to perform a manual action in Mimics.
    
    Parameters:
        split (bool): If True, prompts user to manually split the mask.
        fill (bool): If True, prompts user to manually fill holes.
        title (str): Window title.
    """
    root = tk.Tk()
    root.withdraw()  # Hide main window

    top = tk.Toplevel(root)
    top.title(title)
    top.geometry("350x150")
    top.attributes("-topmost", True)

    if split:
        message = "Please manually split the mask into: 'Left Pelvis', 'Right Pelvis', and 'Other Bones'"
    elif fill:
        message = "Please manually fill any holes in Mimics. Names : 'Left Pelvis Corrected' or 'Right Pelvis Corrected' "
    else:
        message = "Please perform the required manual action in Mimics."

    label1 = tk.Label(top, text=message, wraplength=320, justify="center")
    label1.pack(pady=10)

    label2 = tk.Label(top, text="Click 'Finish' to continue.")
    label2.pack(pady=5)

    finish_button = tk.Button(top, text="Finish", command=top.destroy)
    finish_button.pack(pady=10)

    top.protocol("WM_DELETE_WINDOW", top.destroy)

    root.wait_window(top)
    root.destroy()

def segment_and_export_pelvis(dicom_dir, export_dir, params):
    """
    AIM:
    - Automatically segment the left and right parts of the pelvis from a full CT threshold mask
    - Clean the segmentation using region growing and smart fill
    - Wrap and smooth the resulting 3D parts
    - Export both parts as STL files

    INPUTS:
    - dicom_dir (str): Path to the folder containing DICOM files
    - export_dir (str): Folder where STL files will be saved
    - params (dict): Dictionary with processing parameters, including:
        - threshold_min, threshold_max
        - hole_closing_distance_2
        - wrap_smallest_detail, wrap_gap_closing_distance
        - smooth_factor, smooth_iterations
        - subject, numero

    OUTPUTS:
    - Two STL files: "pelvis_left.stl" and "pelvis_right.stl" saved in the export_dir
    - Mimics project file (.mcs) saved in the working directory
    """

    # 1 - Collect DICOM file paths
    dicom_dir = r"E:\IMAGES"
    input_path = []
    for root, _, files in os.walk(dicom_dir):
        input_path.extend(os.path.join(root, f) for f in files)

    # 2 - Import and configure DICOM images in Mimics
    image_objs = mimics.file.test_images(filenames=input_path, force_raw_import=False)
    print(len(image_objs))

    # Configure the imported DICOM images
    conf_images = mimics.file.configure_dicom_images(imagefiles=image_objs)
    print(len(conf_images)) 

    # 3 - Group images into studies and find the correct series
    studies = mimics.file.split_images_into_studies(configured_imagefiles=conf_images,
                                                        patient_name_grouping=True,
                                                        series_description_grouping=True,
                                                        study_description_grouping=True,
                                                        variable_slice_distance_grouping=True)
    print(len(studies))

    # Function to check if the description matches the desired keywords
    def match_keywords(text):
        text = text.lower().replace(",", ".")  # unifier les virgules en points
        normalized_text = re.sub(r'\s+', '', text)  # supprimer les espaces pour comparer facilement "1mm" et "1 mm"
        
        has_ap = "ap" in text
        has_portal = "portal" in text
        has_resolution = any(unit in normalized_text for unit in ["0.6mm", "1mm"])
        
        return has_ap and has_portal and has_resolution


    # Search for the series matching the keywords
    selected_study = None
    print("Available SeriesDescriptions:")
    for study in studies:
        for image in study.get_images():
            tags = study.get_dicom_tags(i_image_index=0)
            series_description = str(tags.get((0x0008, 0x103e), "")).strip()  # SeriesDescription
            print("→", series_description)

            if match_keywords(series_description):
                print("Matching series found:", series_description)
                selected_study = study
                break
        if selected_study:
            break

    # 4 - Load and open selected study
    if selected_study:
        image_data = mimics.file.load_series_into_memory(studies=[selected_study])
        print("Selected study:", selected_study.get_study_str(include_id=True))
        mimics.file.open_images_as_project(imagedata=image_data)
    else:
        raise ValueError("No matching series found based on SeriesDescription.")

    # 5 - Create global bone mask using threshold
    global_mask = mimics.segment.create_mask()
    global_mask.name = "Full Anatomy"
    mimics.segment.threshold(mask=global_mask, threshold_min=params["threshold_min"], threshold_max=params["threshold_max"])

    # 6 - Region growing to isolate relevant bone
    point = mimics.analyze.indicate_point(title="Region growing point",message="Please indicate a point on the part of interest")
    region_grow_mask = mimics.segment.region_grow(global_mask, target_mask=None,point= point, slice_type="Coronal", keep_original_mask=True, multiple_layer=True, connectivity='6-connectivity')
    region_grow_mask.name = "Only Bones"

    # 7 - Prompt user to manually split masks
    wait_for_user_action(split=True, title="Manual Split Required")

    # 8 - Retrieve manually created masks
    left_mask = mimics.data.masks["Left Pelvis"]
    right_mask= mimics.data.masks["Right Pelvis"]

    # 9 - Fill holes in left pelvis mask
    left_filled = mimics.segment.smart_fill_global(mask=left_mask, hole_closing_distance=params["hole_closing_distance_2"])
    left_filled.name = "Left Pelvis (Filled)"
    
    response_left = mimics.dialogs.question_box(
        "Do you want to manually correct the left pelvis fill?",
        buttons="Yes;No",
    )
    if response_left == "Yes":
        wait_for_user_action(fill=True, title="Manual Correction - Left Pelvis")
        left_filled=mimics.data.masks["Left Pelvis Corrected"]
    
    # Fill holes in right pelvis mask
    right_filled = mimics.segment.smart_fill_global(mask=right_mask, hole_closing_distance=params["hole_closing_distance_2"])
    right_filled.name = "Right Pelvis (Filled)"
    
    response_right = mimics.dialogs.question_box(
        "Do you want to manually correct the left pelvis fill?",
        buttons="Yes;No",
    )
    if response_right == "Yes":
        wait_for_user_action(fill=True, title="Manual Correction - Right Pelvis")
        right_filled=mimics.data.masks["Right Pelvis Corrected"]


    # 10 - Function to wrap and smooth a 3D part from a mask
    def wrap_and_smooth(mask, name):
        part = mimics.segment.calculate_part(mask, quality="Optimal")
        part = mimics.tools.wrap(part, smallest_detail=params["wrap_smallest_detail"], gap_closing_distance=params["wrap_gap_closing_distance"],
                                 keep_originals=False)
        part = mimics.tools.smooth(part, smooth_factor=params["smooth_factor"], iterations=params["smooth_iterations"],
                                   compensate_shrinkage=False, keep_originals=False)
        part.name = name
        return part

    # Create clean 3D parts from filled masks
    left_part = wrap_and_smooth(left_filled, "Left Pelvis Part")
    right_part = wrap_and_smooth(right_filled, "Right Pelvis Part")

    # 11 - Export STL files
    subject_dir = os.path.join(export_dir, f"{params['subject']}_{params['numero']}")
    os.makedirs(subject_dir, exist_ok=True)

    # Export each pelvis part as a separate STL file
    mimics.file.export_part(object_to_convert=left_part, file_name=os.path.join(subject_dir, "pelvis_left.stl"))
    mimics.file.export_part(object_to_convert=right_part, file_name=os.path.join(subject_dir, "pelvis_right.stl"))

    # 12 - Save Mimics project
    f= os.path.join(os.getcwd(), f"{subject}_{numero}.mcs")
    t = "Mimics Project Files"
    mimics.file.save_project(filename=f, save_as_type=t)

    mimics.file.exit()

if __name__ == "__main__":
    # Define subject and numero dynamically, e.g., based on the current project
    subject = "Subject"
    numero = "11"
    
    # Build the path to the JSON files
    subject_dir = os.path.join(os.getcwd(), f"{subject}_{numero}")
    params_mimics_path = os.path.join(subject_dir, "params_mimics.json")
    params_mimics_details_path = os.path.join(subject_dir, "params_mimics_details.json")

    # Load the JSON files dynamically
    with open(params_mimics_path, "r") as f:
        paths = json.load(f)
    
    with open(params_mimics_details_path, "r") as f:
        settings = json.load(f)

    # Call the function with the paths and settings
    dicom_dir=paths["dicom_dir"]
    segment_and_export_pelvis(dicom_dir, paths["export_dir"], settings)
