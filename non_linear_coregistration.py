import os
import glob
from pathlib import Path
import ants
import time
import shutil

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = '/mnt/Data/AKIB/Training data'
PATIENT_IDS = range(1, 51)  # Patients 1 through 50
SOURCES = ['3T', '64mT']
MODALITIES_TO_ALIGN = ['T2', 'FLAIR']  # These are the MOVING images
FIXED_MODALITY = 'T1'                  # This is the FIXED (Reference) image

# ANTs SyN Parameters (Standard, high-accuracy settings for T1/T2 alignment)
# SyN
SYN_TRANSFORM = 'SyN[0.1, 3.0, 0.0]' 
# Multi-resolution structure: 4 levels of optimization
CONVERGENCE = '[100x70x50x20, 1e-6, 10]' # Iterations per level, Convergence Threshold, Patience
SHRINK_FACTORS = '8x4x2x1'               # Shrinking factor per level
SMOOTHING_SIGMAS = '3x2x1x0vox'          # Smoothing sigma per level (in voxels)
# Metric: Mutual Information (MI) is best for multi-modal (T1 vs T2/FLAIR)
METRIC = 'MI' 
# Affine Transform (precedes SyN)
AFFINE_TRANSFORM = 'Affine[0.1]'


# ============================================================================
# ANTs Registration Helper (using ANTsPy)
# ============================================================================

def perform_syn_registration(fixed_path, moving_path, output_prefix, moving_modality):
    """
    Performs SyN non-linear registration using ANTsPy.
    
    Args:
        fixed_path: Path to fixed (reference) image
        moving_path: Path to moving image
        output_prefix: Prefix for output files
        moving_modality: Name of moving modality (for logging)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"      → Loading images...")
        fixed = ants.image_read(fixed_path)
        moving = ants.image_read(moving_path)
        
        print(f"      → Performing SyN registration (this may take several minutes)...")
        start_time = time.time()
        
        # Perform registration with SyN
        registration = ants.registration(
            fixed=fixed,
            moving=moving,
            type_of_transform='SyN',  # Symmetric Normalization (non-linear)
            aff_metric='mattes',       # Mutual Information for affine stage
            syn_metric='mattes',       # Mutual Information for SyN stage
            aff_sampling=32,           # Sampling for affine
            syn_sampling=32,           # Sampling for SyN
            reg_iterations=(100, 70, 50, 20),  # Multi-resolution iterations
            aff_iterations=(1000, 500, 250, 100),  # Affine iterations
            verbose=False
        )
        
        elapsed = time.time() - start_time
        
        # Save the warped image
        output_image = output_prefix + 'Warped.nii.gz'
        ants.image_write(registration['warpedmovout'], output_image)
        
        # Save transforms (use shutil.move for cross-device compatibility)
        # Forward transform (moving -> fixed)
        fwd_transform = output_prefix + '1Warp.nii.gz'
        if len(registration['fwdtransforms']) > 0 and os.path.exists(registration['fwdtransforms'][0]):
            shutil.move(registration['fwdtransforms'][0], fwd_transform)
        
        # Affine transform
        affine_transform = output_prefix + '0GenericAffine.mat'
        if len(registration['fwdtransforms']) > 1 and os.path.exists(registration['fwdtransforms'][1]):
            shutil.move(registration['fwdtransforms'][1], affine_transform)
        
        # Inverse transforms (optional, but useful)
        if len(registration['invtransforms']) > 0:
            inv_warp = output_prefix + '1InverseWarp.nii.gz'
            if os.path.exists(registration['invtransforms'][0]):
                shutil.move(registration['invtransforms'][0], inv_warp)
        
        print(f"      ✓ Registration successful (Time: {elapsed:.1f}s)")
        print(f"        Output: {output_image}")
        return True
        
    except Exception as e:
        print(f"      ✗ ERROR during registration: {str(e)}")
        return False


# ============================================================================
# MAIN PROCESSING LOOP
# ============================================================================

def non_linear_co_registration():
    """Performs ANTs SyN non-linear co-registration of T2/FLAIR to T1."""

    print("\n" + "="*80)
    print("STEP 5: ANTS SYMMETRIC NORMALIZATION (SYN) CO-REGISTRATION")
    print("="*80)
    print(f"Fixed Modality (Reference): {FIXED_MODALITY}")
    print(f"Moving Modalities: {', '.join(MODALITIES_TO_ALIGN)}")
    print(f"Using ANTsPy for registration")
    
    total_registrations = 0
    successful = 0
    failed = 0
    skipped = 0
    
    start_time = time.time()

    for patient_id in PATIENT_IDS:
        p_str = str(patient_id)
        
        for source in SOURCES:
            patient_dir = os.path.join(BASE_DIR, p_str, source)
            print(f"\n  Processing Patient {p_str}, Source {source}")

            # Define the FIXED image (T1) path
            # Using MNI brain-extracted image as reference (final preprocessing stage)
            FIXED_IMAGE = os.path.join(patient_dir, f'{p_str}_{FIXED_MODALITY}_MNI_brain.nii.gz')

            if not os.path.exists(FIXED_IMAGE):
                print(f"    WARNING: Fixed T1 image not found at {FIXED_IMAGE}. Skipping source.")
                continue

            for moving_modality in MODALITIES_TO_ALIGN:
                
                total_registrations += 1
                
                # Define the MOVING image (T2 or FLAIR) path
                # Using MNI brain-extracted image for alignment
                MOVING_IMAGE = os.path.join(patient_dir, f'{p_str}_{moving_modality}_MNI_brain.nii.gz')
                
                if not os.path.exists(MOVING_IMAGE):
                    print(f"      WARNING: Moving {moving_modality} image not found. Skipping.")
                    failed += 1
                    continue

                # Define ANTs output paths
                OUTPUT_PREFIX = os.path.join(patient_dir, f'{p_str}_{moving_modality}_to_T1_')
                OUTPUT_IMAGE = OUTPUT_PREFIX + 'Warped.nii.gz'
                
                # Skip if already processed
                if os.path.exists(OUTPUT_IMAGE):
                    print(f"      SKIP: Non-linear output for {moving_modality} already exists.")
                    skipped += 1
                    continue

                # Perform registration using ANTsPy
                print(f"    → Registering {moving_modality} to {FIXED_MODALITY}...")
                success = perform_syn_registration(
                    FIXED_IMAGE, 
                    MOVING_IMAGE, 
                    OUTPUT_PREFIX,
                    moving_modality
                )
                
                if success:
                    successful += 1
                else:
                    failed += 1
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("STEP 5 COMPLETE: Non-Linear Co-registration Finished.")
    print("="*80)
    print(f"Total registrations attempted: {total_registrations}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"⊘ Skipped (already exist): {skipped}")
    print(f"⏱  Total time: {elapsed_time/60:.2f} minutes")
    print("="*80)
    print("T1, T2, and FLAIR modalities are now precisely aligned.")
    print("="*80)


if __name__ == "__main__":
    non_linear_co_registration()