# Mimics_automation
This repository provides a semi-automated pipeline to perform 3D segmentation, meshing, and curvature analysis of pelvic bone structures from DICOM medical images. The workflow leverages the Python APIs of Materialise Mimics and 3-Matic.

Project structure:
- run.py : One-click launcher for the full workflow

- liaison.py : Handles parameters and coordinates Mimics + 3-Matic execution

- mimics.py : Segmentation logic for pelvic structures in Mimics

- matic.py : Mesh processing and curvature analysis in 3-Matic


Inputs : 
- DICOM files (pelvis CT scans)

- Automatically generated JSON configuration files


Outputs : 
- pelvis_left.stl, pelvis_right.stl – 3D bone meshes

- curvature_left.txt, curvature_right.txt – surface curvature data

- .mcs and .mxp project files (for Mimics and 3-Matic)


User interaction required : 
- Place a seed point for Region Growing

- Use Split Mask to isolate anatomical parts

- (Optional) refine masks with Smart Fill if segmentation is imperfect

  
