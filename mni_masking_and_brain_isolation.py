import subprocess
import os
import glob
import SimpleITK as sitk
from pathlib import Path

# --- Configuration based on conversation history ---

BASE_DIR = '/mnt/Data/AKIB/Training data'
PATIENT_IDS = range(1, 51)  
SOURCES = ['3T', '64mT']
MODALITIES = ['T1', 'T2', 'FLAIR']

# Template path (used as reference for both transformation and final output size)
FSL_DATA_DIR = os.environ.get('FSLDIR', '/usr/local/fsl')
REFERENCE_TEMPLATE = '/mnt/code/AKIB/Hybrid3DSRCycleGAN/MNI152_T1_1mm.nii.gz'

# --- FSL Command Execution Helper ---

def run_fsl_command(command, description):
    """Executes an FSL command using subprocess."""
    print(f"      → {description}...")
    try:
        # We assume FSL binaries (like flirt, fslmaths) are in the system PATH
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"      ✓ {description} successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"      ✗ FATAL ERROR during {description}.")
        print(f"        Command: {' '.join(command)}")
        print(f"        STDERR:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"      ✗ FATAL ERROR: Required binary (e.g., {command}) not found.")
        print("        Ensure FSL and c3d_affine_tool are installed and in your PATH.")
        return False


# --- Main Final Masking Loop (Step 4) ---

def final_masking_step():
    """Applies the MNI transformation to the mask and uses it to isolate the brain."""
    
    print("\n" + "="*80)
    print("STEP 4: FINAL MASKING AND BRAIN ISOLATION")
    print("="*80)

    for patient_id in PATIENT_IDS:
        p_str = str(patient_id)
        
        for source in SOURCES:
            patient_dir = os.path.join(BASE_DIR, p_str, source)
            print(f"\n  Processing Patient {p_str}, Source {source}")

            # Define static paths needed for this step
            MASK_INPUT = os.path.join(patient_dir, f'{p_str}_FLAIR_bet_mask.nii.gz')
            
            if not os.path.exists(MASK_INPUT):
                print(f"    WARNING: FLAIR Brain Mask not found at {MASK_INPUT}. Skipping source.")
                continue

            for modality in MODALITIES:
                print(f"    Processing Modality: {modality}")

                # Paths from Step 3 (Linear Registration Output)
                MNI_FULLHEAD_REGISTERED = os.path.join(patient_dir, f'{p_str}_{modality}_MNI_registered_fullhead.nii.gz')
                TRANSFORM_TFM = os.path.join(patient_dir, f'{p_str}_{modality}_MNI_fullhead_transform.tfm')
                
                # Paths for intermediate and final outputs
                TRANSFORM_FSL_MAT = os.path.join(patient_dir, f'{p_str}_{modality}_MNI_fullhead.mat')
                MNI_WARPED_MASK = os.path.join(patient_dir, f'{p_str}_{modality}_MNI_mask.nii.gz')
                FINAL_MNI_BRAIN = os.path.join(patient_dir, f'{p_str}_{modality}_FINAL_MNI.nii.gz')

                if not os.path.exists(TRANSFORM_TFM) or not os.path.exists(MNI_FULLHEAD_REGISTERED):
                    print(f"      ✗ SKIP: Step 3 output missing (TFM or registered full head image).")
                    continue
                
                # --- 4a. Convert SimpleITK (.tfm) Transform to FSL (.mat) ---
                # FSL tools require the matrix in FSL format (4x4 text file).
                # This conversion uses c3d_affine_tool, assuming it is installed.
                convert_command = [
                    'c3d_affine_tool',
                    '-ref', REFERENCE_TEMPLATE,
                    '-src', MNI_FULLHEAD_REGISTERED,
                    TRANSFORM_TFM,
                    '-fsl', TRANSFORM_FSL_MAT,
                    '-oitk', TRANSFORM_TFM  # Keep the original .tfm file
                ]
                
                if not run_fsl_command(convert_command, "Converting SimpleITK TFM to FSL MAT"):
                    continue

                # --- 4b. Apply FSL Transformation to the Brain Mask ---
                # We use nearest neighbor interpolation ('nn') for binary masks to preserve edges.
                applyxfm_mask_command = [
                    'flirt',
                    '-applyxfm',
                    '-in', MASK_INPUT,
                    '-ref', REFERENCE_TEMPLATE,
                    '-out', MNI_WARPED_MASK,
                    '-init', TRANSFORM_FSL_MAT,
                    '-interp', 'nearestneighbour'
                ]
                
                if not run_fsl_command(applyxfm_mask_command, "Applying transformation to mask"):
                    continue
                    
                # --- 4c. Mask the Registered Full Head Image ---
                # Multiply the registered full head image by the warped mask (element-wise multiplication)
                mask_image_command = [
                    'fslmaths',
                    MNI_FULLHEAD_REGISTERED,
                    '-mul', MNI_WARPED_MASK,
                    FINAL_MNI_BRAIN
                ]
                
                if not run_fsl_command(mask_image_command, "Applying MNI mask to image"):
                    continue
                
                print(f"      ★★ FINAL OUTPUT: {FINAL_MNI_BRAIN} saved. ★★")

    print("\n" + "="*80)
    print("FINAL MASKING COMPLETE. Data is now standardized and ready for GAN input.")
    print("="*80)


if __name__ == "__main__":
    final_masking_step()