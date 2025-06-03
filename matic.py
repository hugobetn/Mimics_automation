import os
import json
import shutil

def analyze_curvature_and_export(
    stl_l, stl_r, export_dir,
    target_edge_length=1.3, volume_max_edge_length=1.5):
    """
    Perform curvature analysis on a specified part from a 3-matic project and export the results.

     AIM:
    - Import left and right pelvis STL files into 3-matic
    - Apply uniform remeshing to normalize surface geometry
    - Generate volume mesh (tetrahedral) for simulation use
    - Perform maximum curvature analysis on each part
    - Export the analysis results as .txt files for left and right pelvis
    - Save a new 3-matic project including the results

    INPUTS:
    - stl_l (str): Full path to the STL file of the left pelvis
    - stl_r (str): Full path to the STL file of the right pelvis
    - export_dir (str): Directory where analysis results and project will be saved
    - target_edge_length (float, optional): Desired triangle edge length for remeshing
    - volume_max_edge_length (float, optional): Maximum edge length for volume mesh generation

    OUTPUTS:
    - curvature_left.txt and curvature_right.txt in export_dir
    - project_curvature_and_mesh.mxp saved in export_dir
    """

    # 1 – Check if export directory exists
    if not os.path.exists(export_dir):
        raise ValueError(f"Répertoire d'export inexistant : {export_dir}")

    # 2 – Import STL parts (left and right pelvis)
    part_l = trimatic.import_part_stl(stl_l)
    part_l.name = "Pelvis Left"

    part_r = trimatic.import_part_stl(stl_r)
    part_r.name = "Pelvis Right"

    # 3 – Remesh the left pelvis
    print("Traitement du pelvis gauche...")
    trimatic.uniform_remesh(entities=part_l, target_triangle_edge_length=target_edge_length, preserve_surface_contours=True)

    # 4 - Step 4 – Generate volume mesh for left pelvis
    print("Génération du maillage volumique gauche...")
    mesh_l = trimatic.create_volume_mesh(part_l,element_type=trimatic.ElementType.Tet4,maximum_edge_length=volume_max_edge_length)
    mesh_l.name = "Pelvis_Left_TetraMesh"

    # 5 – Perform curvature analysis on left pelvis
    analysis_l = trimatic.create_maximum_curvature_analysis(part_l)
    trimatic.export_analysis(analysis_l, export_dir)

    # 6 – Rename left curvature export file
    exported_left_file = os.path.join(export_dir, "AnalysisResults.txt")
    renamed_left_file = os.path.join(export_dir, "curvature_left.txt")
    if os.path.exists(exported_left_file):
        shutil.move(exported_left_file, renamed_left_file)

    # 7 – Repeat steps for the right pelvis
    print("Traitement du pelvis droit...")
    trimatic.uniform_remesh(entities=part_r, target_triangle_edge_length=target_edge_length, preserve_surface_contours=True)
    
    print("Génération du maillage volumique droit...")
    mesh_r = trimatic.create_volume_mesh(part_r,element_type=trimatic.ElementType.Tet4,maximum_edge_length=volume_max_edge_length)
    mesh_r.name = "Pelvis_Right_TetraMesh"
    analysis_r = trimatic.create_maximum_curvature_analysis(part_r)
    trimatic.export_analysis(analysis_r, export_dir)

    exported_right_file = os.path.join(export_dir, "AnalysisResults.txt")
    renamed_right_file = os.path.join(export_dir, "curvature_right.txt")
    if os.path.exists(exported_right_file):
        shutil.move(exported_right_file, renamed_right_file)

    # 8 – Save updated 3-matic project
    project_save_path = os.path.join(export_dir, "project_curvature_and_mesh.mxp")
    trimatic.save_project(project_save_path)

    print(f"Projet 3-matic sauvegardé avec succès à : {project_save_path}")

    print("Analyse de courbure et maillage terminés pour les deux pelvis.")

    # 9 – Exit 3-matic
    trimatic.exit()

if __name__ == "__main__":
    # Sujet et numéro
    subject = "Subject"
    numero = "11"

    subject_folder = os.path.join(os.getcwd(), f"{subject}_{numero}")
    params_3matic_path = os.path.join(subject_folder, "params_3matic.json")
    params_3matic_details_path = os.path.join(subject_folder, "params_3matic_details.json")

    # Vérifier les fichiers
    if not os.path.exists(params_3matic_path):
        print(f"Erreur : {params_3matic_path} introuvable.")
    else:
        with open(params_3matic_path, "r") as f:
            params = json.load(f)

        with open(params_3matic_details_path, "r") as f:
            params_details = json.load(f)

        analyze_curvature_and_export(
            stl_l=params["stl_l"],
            stl_r=params["stl_r"],
            export_dir=params["export_dir"],
            target_edge_length=params_details["target_edge_length"],
            volume_max_edge_length=params_details["volume_max_edge_length"]
        )
