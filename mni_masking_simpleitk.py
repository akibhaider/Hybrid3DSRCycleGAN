#!/usr/bin/env python3
"""
MNI Brain Masking using SimpleITK (Alternative to FSL-based approach)

This script applies brain masks to MNI-registered images using only SimpleITK,
avoiding the need for FSL and c3d_affine_tool.

Since the images are already in MNI space, we can:
1. Resample the original mask to MNI space using the existing transform
2. Apply the resampled mask to the MNI-registered image
"""

import os
import SimpleITK as sitk
import numpy as np
from pathlib import Path

# --- Configuration ---
BASE_DIR = '/mnt/Data/AKIB/Training data'
PATIENT_IDS = range(1, 51)  
SOURCES = ['3T', '64mT']
MODALITIES = ['T1', 'T2', 'FLAIR']

# MNI template (used as reference space)
REFERENCE_TEMPLATE = '/mnt/code/AKIB/Hybrid3DSRCycleGAN/MNI152_T1_1mm_brain.nii.gz'

# Statistics tracking
stats = {
    'total': 0,
    'successful': 0,
    'failed': 0,
    'missing_input': 0,
    'errors': []
}


def apply_mask_to_mni_image(patient_id, source, modality):
    """
    Apply brain mask to MNI-registered image.
    
    Steps:
    1. Load original mask (in native space)
    2. Load MNI-registered image
    3. Load transform file
    4. Resample mask to MNI space using the transform
    5. Apply mask to MNI image (element-wise multiplication)
    """
    p_str = str(patient_id)
    patient_dir = os.path.join(BASE_DIR, p_str, source)
    
    # Input paths
    mask_path = os.path.join(patient_dir, f'{p_str}_{modality}_bet_mask.nii.gz')
    mni_image_path = os.path.join(patient_dir, f'{p_str}_{modality}_MNI_registered.nii.gz')
    transform_path = os.path.join(patient_dir, f'{p_str}_{modality}_MNI_transform.tfm')
    
    # Output path
    output_path = os.path.join(patient_dir, f'{p_str}_{modality}_MNI_brain.nii.gz')
    
    # Check if output already exists
    if os.path.exists(output_path):
        print(f"      ⚠ SKIP: Output already exists: {output_path}")
        stats['successful'] += 1
        return True
    
    # Check if all inputs exist
    if not os.path.exists(mask_path):
        print(f"      ✗ SKIP: Mask not found: {mask_path}")
        stats['missing_input'] += 1
        return False
    
    if not os.path.exists(mni_image_path):
        print(f"      ✗ SKIP: MNI image not found: {mni_image_path}")
        stats['missing_input'] += 1
        return False
    
    if not os.path.exists(transform_path):
        print(f"      ✗ SKIP: Transform not found: {transform_path}")
        stats['missing_input'] += 1
        return False
    
    try:
        # Load images
        print(f"      → Loading mask...")
        mask_img = sitk.ReadImage(mask_path)
        
        print(f"      → Loading MNI-registered image...")
        mni_img = sitk.ReadImage(mni_image_path)
        
        print(f"      → Loading transform...")
        transform = sitk.ReadTransform(transform_path)
        
        # Load reference template to ensure consistent space
        reference_img = sitk.ReadImage(REFERENCE_TEMPLATE)
        
        # Resample mask to MNI space using the same transform
        print(f"      → Resampling mask to MNI space...")
        mask_resampled = sitk.Resample(
            mask_img,           # Moving image (mask)
            reference_img,      # Reference image (MNI template)
            transform,          # Transform from native to MNI
            sitk.sitkNearestNeighbor,  # Nearest neighbor for binary mask
            0.0,                # Default pixel value (outside FOV)
            mask_img.GetPixelID()
        )
        
        # Ensure mask is binary (0 or 1)
        print(f"      → Binarizing mask...")
        mask_binary = sitk.BinaryThreshold(
            mask_resampled,
            lowerThreshold=0.5,
            upperThreshold=1e9,
            insideValue=1,
            outsideValue=0
        )
        mask_binary = sitk.Cast(mask_binary, sitk.sitkUInt8)
        
        # Apply mask to MNI image (element-wise multiplication)
        print(f"      → Applying mask to MNI image...")
        masked_mni = sitk.Mask(mni_img, mask_binary, outsideValue=0, maskingValue=0)
        
        # Save result
        print(f"      → Saving masked brain image...")
        sitk.WriteImage(masked_mni, output_path)
        
        # Verify output
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"      ✓ SUCCESS: Saved {output_path} ({file_size:.2f} MB)")
            stats['successful'] += 1
            return True
        else:
            print(f"      ✗ FAIL: Output file not created")
            stats['failed'] += 1
            return False
            
    except Exception as e:
        error_msg = f"Patient {p_str}, {source}, {modality}: {str(e)}"
        print(f"      ✗ ERROR: {str(e)}")
        stats['errors'].append(error_msg)
        stats['failed'] += 1
        return False


def main():
    """Main processing loop."""
    print("\n" + "="*80)
    print("MNI BRAIN MASKING USING SIMPLEITK")
    print("="*80)
    print(f"Processing {len(PATIENT_IDS)} patients × {len(SOURCES)} sources × {len(MODALITIES)} modalities")
    print(f"Reference template: {REFERENCE_TEMPLATE}")
    print("="*80 + "\n")
    
    # Check if template exists
    if not os.path.exists(REFERENCE_TEMPLATE):
        print(f"✗ ERROR: Reference template not found: {REFERENCE_TEMPLATE}")
        print("Please ensure the MNI template is available.")
        return
    
    # Process all combinations
    for patient_id in PATIENT_IDS:
        p_str = str(patient_id)
        
        for source in SOURCES:
            patient_dir = os.path.join(BASE_DIR, p_str, source)
            
            if not os.path.isdir(patient_dir):
                print(f"⚠ WARNING: Patient directory not found: {patient_dir}")
                continue
            
            print(f"\n📁 Patient {p_str}, Source: {source}")
            
            for modality in MODALITIES:
                print(f"  🧠 Processing {modality}...")
                stats['total'] += 1
                apply_mask_to_mni_image(patient_id, source, modality)
    
    # Print summary
    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"Total images processed: {stats['total']}")
    print(f"✓ Successful: {stats['successful']}")
    print(f"✗ Failed: {stats['failed']}")
    print(f"⚠ Missing input: {stats['missing_input']}")
    
    if stats['errors']:
        print(f"\n⚠ Errors encountered ({len(stats['errors'])}):")
        for i, error in enumerate(stats['errors'][:10], 1):
            print(f"  {i}. {error}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")
    
    print("="*80)
    print(f"\n✅ Final brain-extracted files saved as: *_MNI_brain.nii.gz")
    print(f"   These files are brain-only images in standard MNI space.")
    print("="*80 + "\n")


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    main()
    
    elapsed = time.time() - start_time
    print(f"⏱️  Total time: {elapsed/60:.2f} minutes")
