import os
import SimpleITK as sitk
import numpy as np
from pathlib import Path
import time

# ============================================================================
# CONFIGURATION (MODIFIED)
# ============================================================================

BASE_DIR = '/mnt/Data/AKIB/Training data'

# Use the brain-extracted MNI template (this is what we have available)
# Note: For best results with full-head images, a full-head template would be ideal,
# but the brain template will still work for alignment
TEMPLATE_PATH = '/mnt/code/AKIB/Hybrid3DSRCycleGAN/MNI152_T1_1mm_brain.nii.gz'

# Dataset parameters
PATIENT_IDS = range(1, 51)  # Patients 1 to 50
SOURCES = ['3T', '64mT']
MODALITIES = ['T1', 'T2', 'FLAIR']

# Registration parameters
REGISTRATION_METHOD = 'rigid'  # 6 DOF: 3 translations + 3 rotations
INTERPOLATION = sitk.sitkLinear
NUMBER_OF_ITERATIONS = 200
LEARNING_RATE = 1.0
MIN_STEP = 0.001
RELAXATION_FACTOR = 0.5

# ============================================================================
# HELPER FUNCTIONS (UNCHANGED)
# ============================================================================

def find_file_with_extensions(path_without_ext):
    """Try to find file with.nii.gz or.nii extension."""
    for ext in ('.nii.gz', '.nii'):
        p = path_without_ext + ext
        if os.path.exists(p):
            return p
    return None


def register_to_mni(moving_image_path, fixed_image_path, output_path, transform_path=None):
    """
    Perform rigid registration of moving image to fixed template.
    
    Args:
        moving_image_path: Path to N4-corrected image to register
        fixed_image_path: Path to MNI template
        output_path: Path to save registered image
        transform_path: Optional path to save transformation matrix
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load images
        fixed = sitk.ReadImage(fixed_image_path, sitk.sitkFloat32)
        moving = sitk.ReadImage(moving_image_path, sitk.sitkFloat32)
        
        # Initialize registration method
        registration = sitk.ImageRegistrationMethod()
        
        # Similarity metric - Mutual Information for multi-modal registration
        registration.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        registration.SetMetricSamplingStrategy(registration.RANDOM)
        registration.SetMetricSamplingPercentage(0.01)
        
        # Interpolator
        registration.SetInterpolator(INTERPOLATION)
        
        # Optimizer - Regular Step Gradient Descent
        registration.SetOptimizerAsRegularStepGradientDescent(
            learningRate=LEARNING_RATE,
            minStep=MIN_STEP,
            numberOfIterations=NUMBER_OF_ITERATIONS,
            relaxationFactor=RELAXATION_FACTOR
        )
        registration.SetOptimizerScalesFromPhysicalShift()
        
        # Setup for multi-resolution framework
        registration.SetShrinkFactorsPerLevel(shrinkFactors=[1, 2, 3])
        registration.SetSmoothingSigmasPerLevel(smoothingSigmas=[0, 1, 2])
        registration.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
        
        # Initial transform - Rigid (Euler3D) for 6 DOF
        initial_transform = sitk.CenteredTransformInitializer(
            fixed,
            moving,
            sitk.Euler3DTransform(),
            sitk.CenteredTransformInitializerFilter.GEOMETRY
        )
        registration.SetInitialTransform(initial_transform, inPlace=False)
        
        # Execute registration
        final_transform = registration.Execute(fixed, moving)
        
        # Apply transform to moving image
        resampled = sitk.Resample(
            moving,
            fixed,
            final_transform,
            INTERPOLATION,
            0.0,  # Default pixel value
            moving.GetPixelID()
        )
        
        # Save registered image
        sitk.WriteImage(resampled, output_path)
        
        # Optionally save transformation
        if transform_path:
            sitk.WriteTransform(final_transform, transform_path)
        
        # Print registration metrics
        print(f"    ✓ Final metric value: {registration.GetMetricValue():.4f}")
        print(f"    ✓ Optimizer stop condition: {registration.GetOptimizerStopConditionDescription()}")
        
        return True
        
    except Exception as e:
        print(f"    ✗ ERROR: {str(e)}")
        return False


# ============================================================================
# MAIN PROCESSING (MODIFIED)
# ============================================================================

def main():
    """Main processing function to register all N4-corrected images."""
    
    print("="*80)
    print("LINEAR REGISTRATION TO MNI152 TEMPLATE")
    print("="*80)
    print(f"\nBase directory: {BASE_DIR}")
    print(f"Template: {TEMPLATE_PATH}")
    print(f"Patients: {min(PATIENT_IDS)} to {max(PATIENT_IDS)}")
    print(f"Sources: {', '.join(SOURCES)}")
    print(f"Modalities: {', '.join(MODALITIES)}")
    print(f"Registration: {REGISTRATION_METHOD.upper()} (6 DOF)")
    print(f"Iterations: {NUMBER_OF_ITERATIONS}")
    print()
    
    # Check if template exists
    if not os.path.exists(TEMPLATE_PATH):
        print(f"ERROR: Template not found at {TEMPLATE_PATH}")
        print("Please ensure MNI152_T1_1mm_brain.nii.gz is available.")
        return
    
    # Statistics
    stats = {
        'total': 0,
        'successful': 0,
        'failed': 0,
        'missing_input': 0,
        'errors': []
    }
    
    start_time = time.time()
    
    # Process each patient, source, and modality
    for patient_id in PATIENT_IDS:
        print(f"\n{'='*80}")
        print(f"Processing Patient {patient_id}")
        print(f"{'='*80}")
        
        for source in SOURCES:
            print(f"\n  Source: {source}")
            
            for modality in MODALITIES:
                stats['total'] += 1
                
                # Construct file paths
                patient_dir = os.path.join(BASE_DIR, str(patient_id), source)
                
                # Input is the N4-Corrected image (full head from bias correction)
                n4_base = os.path.join(patient_dir, f'{patient_id}_{modality}_N4corrected')
                n4_path = find_file_with_extensions(n4_base)
                
                # Output paths for registered images
                output_path = os.path.join(patient_dir, f'{patient_id}_{modality}_MNI_registered.nii.gz')
                transform_path = os.path.join(patient_dir, f'{patient_id}_{modality}_MNI_transform.tfm')
                
                print(f"    Processing {modality}...")
                print(f"      Input: {n4_path if n4_path else 'NOT FOUND'}")
                
                # Check if N4-corrected image exists
                if n4_path is None or not os.path.exists(n4_path):
                    print(f"      ✗ SKIP: N4-corrected image not found")
                    stats['missing_input'] += 1
                    continue
                
                # Check if already processed
                if os.path.exists(output_path):
                    print(f"      ⚠ SKIP: Already registered (output exists)")
                    stats['successful'] += 1  # Count as successful
                    continue
                
                # Perform registration
                print(f"      → Registering to MNI space...")
                success = register_to_mni(
                    n4_path,
                    TEMPLATE_PATH,
                    output_path,
                    transform_path
                )
                
                if success:
                    stats['successful'] += 1
                    print(f"      ✓ Saved: {output_path}")
                    print(f"      ✓ Transform: {transform_path}")
                else:
                    stats['failed'] += 1
                    stats['errors'].append((patient_id, source, modality))
    
    # Print summary
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("REGISTRATION SUMMARY")
    print("="*80)
    print(f"Total images processed: {stats['total']}")
    print(f"  ✓ Successful: {stats['successful']}")
    print(f"  ✗ Failed: {stats['failed']}")
    print(f"  ⚠ Missing input: {stats['missing_input']}")
    print(f"\nTotal time: {elapsed_time/60:.2f} minutes")
    print(f"Average time per image: {elapsed_time/stats['total']:.2f} seconds")
    
    if stats['errors']:
        print(f"\nErrors occurred for {len(stats['errors'])} images:")
        for patient_id, source, modality in stats['errors'][:20]:
            print(f"  - Patient {patient_id}, {source}, {modality}")
        if len(stats['errors']) > 20:
            print(f" ... and {len(stats['errors'])-20} more")
    
    print("\n" + "="*80)
    print("Registration complete!")
    print("="*80)


if __name__ == "__main__":
    main()