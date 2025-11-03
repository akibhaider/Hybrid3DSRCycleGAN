import SimpleITK as sitk
import os
import glob
import numpy as np

# --- Configuration based on user-provided file structure ---

BASE_DIR = '/mnt/Data/AKIB/Training data'
PATIENT_IDS = range(1, 51)  # Patients 1 through 50
# Field strengths / site directories present under each patient folder
FIELD_STRENGTHS = ['3T', '64mT']
# Modalities to process (expect skull-stripped images with suffix '_skullstripped')
MODALITIES = ['T1', 'T2', 'FLAIR']

# --- N4 Bias Field Correction Parameters ---
# These are sensible defaults; tune for your data if needed.
# Maximum number of iterations per multi-resolution level (e.g. coarse->fine)
N4_ITERATIONS = [50, 50, 30]
# The convergence threshold; smaller = more precise but longer runtime
N4_CONVERGENCE_THRESHOLD = 1e-7
# Shrink factor to speed up estimation (apply on downsampled image). 1=full size.
N4_SHRINK_FACTOR = 2
# Spline order used for B-spline fitting (typical is 3)
N4_SPLINE_ORDER = 3

print(f"Starting N4 Bias Field Correction across {len(PATIENT_IDS)} patients, {len(FIELD_STRENGTHS)} sources, and {len(MODALITIES)} modalities...")

# --- Main Processing Loop ---

for patient_id in PATIENT_IDS:
    p_str = str(patient_id)
    print(f"\nProcessing Patient: {p_str}")

    for source in FIELD_STRENGTHS:
        print(f"  Source: {source}")

        # The mask path is assumed to be derived from FLAIR skull-stripping
        mask_filename = f"{p_str}_FLAIR_bet_mask.nii.gz"
        mask_dir = os.path.join(BASE_DIR, p_str, source)
        mask_path = os.path.join(mask_dir, mask_filename)

        if not os.path.exists(mask_path):
            print(f"    WARNING: Mask not found at {mask_path}. Skipping source {source} for patient {p_str}.")
            continue

        try:
            # 1. Load the brain mask
            mask_image = sitk.ReadImage(mask_path)
            # Ensure mask is binary/int type
            mask_image = sitk.Cast(mask_image > 0, sitk.sitkUInt8)
            print(f"    Loaded mask from: {mask_path}")

        except Exception as e:
            print(f"    ERROR reading mask: {mask_path} - {e}. Skipping all modalities for this source.")
            continue

        for modality in MODALITIES:
            # 2. Construct input and output paths
            input_filename = f"{p_str}_{modality}_skullstripped.nii.gz"
            output_filename = f"{p_str}_{modality}_N4corrected.nii.gz"
            
            input_path = os.path.join(BASE_DIR, p_str, source, input_filename)
            output_path = os.path.join(BASE_DIR, p_str, source, output_filename)

            if not os.path.exists(input_path):
                print(f"      WARNING: Input image not found at {input_path}. Skipping {modality}.")
                continue

            if os.path.exists(output_path):
                print(f"      SKIP: Output already exists at {output_path}")
                continue

            try:
                # 3. Load the input image (skull-stripped) and cast to float
                input_image = sitk.ReadImage(input_path)
                input_image = sitk.Cast(input_image, sitk.sitkFloat32)

                # Optionally apply shrink to speed up estimation
                if N4_SHRINK_FACTOR and N4_SHRINK_FACTOR > 1:
                    working_image = sitk.Shrink(input_image, [N4_SHRINK_FACTOR]*input_image.GetDimension())
                    working_mask = sitk.Shrink(mask_image, [N4_SHRINK_FACTOR]*mask_image.GetDimension())
                else:
                    working_image = input_image
                    working_mask = mask_image

                # 4. Initialize and Configure N4 Filter
                corrector = sitk.N4BiasFieldCorrectionImageFilter()
                corrector.SetMaximumNumberOfIterations(N4_ITERATIONS)
                corrector.SetConvergenceThreshold(N4_CONVERGENCE_THRESHOLD)
                corrector.SetSplineOrder(N4_SPLINE_ORDER)

                print(f"      Correcting {modality} image (shrink={N4_SHRINK_FACTOR})...")

                # 5. Execute N4 Correction (on working image/mask)
                output_image = corrector.Execute(working_image, working_mask)

                # If shrink was applied, we need to apply the estimated bias field to the full resolution image
                if N4_SHRINK_FACTOR and N4_SHRINK_FACTOR > 1:
                    # The filter's output is the corrected (downsampled) image; a more correct approach is to
                    # retrieve the log bias field and resample it back to full image, then divide original image.
                    # SimpleITK's N4 filter provides GetLogBiasFieldAsImage()
                    try:
                        log_bias = corrector.GetLogBiasFieldAsImage(input_image)
                        # Exponentiate and divide original image
                        bias_field = sitk.Exp(log_bias)
                        corrected_full = sitk.Divide(input_image, bias_field)
                    except Exception:
                        # Fallback: just resample corrected downsampled image back to original grid
                        corrected_full = sitk.Resample(output_image, input_image)
                else:
                    corrected_full = output_image

                # 6. Save the corrected image
                sitk.WriteImage(corrected_full, output_path)
                print(f"      SUCCESS: Corrected image saved to: {output_path}")

            except Exception as e:
                print(f"      FATAL ERROR during N4 correction for {modality} at {input_path}: {e}")

print("\nN4 Bias Field Correction Pipeline Complete.")