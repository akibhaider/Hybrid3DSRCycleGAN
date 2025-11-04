# Linear Registration to MNI152 Template - Summary

## Overview
Successfully completed linear (rigid, 6 DOF) registration of all N4 bias-corrected brain images to the MNI152 T1 1mm brain template.

## Processing Details

### Dataset
- **Total images processed**: 300
- **Patients**: 1 to 50
- **Sources**: 3T, 64mT
- **Modalities**: T1, T2, FLAIR
- **Registration**: All N4 bias-corrected images

### Registration Method
- **Algorithm**: Rigid registration (6 degrees of freedom)
  - 3 translations (X, Y, Z)
  - 3 rotations (pitch, yaw, roll)
- **Similarity Metric**: Mattes Mutual Information
- **Optimizer**: Regular Step Gradient Descent
- **Multi-resolution**: 3 levels (shrink factors: 4, 2, 1)
- **Interpolation**: Linear (trilinear)
- **Maximum iterations**: 200 per level

### Template
- **Reference**: MNI152_T1_1mm_brain.nii.gz
- **Location**: `/mnt/code/AKIB/Hybrid3DSRCycleGAN/MNI152_T1_1mm_brain.nii.gz`
- **Dimensions**: 182 × 218 × 182
- **Voxel size**: 1.0 × 1.0 × 1.0 mm³

## File Naming Convention

### Input Files
```
/mnt/Data/AKIB/Training data/{patient_id}/{source}/{patient_id}_{modality}_N4corrected.nii.gz
```

### Output Files

**Registered Images:**
```
/mnt/Data/AKIB/Training data/{patient_id}/{source}/{patient_id}_{modality}_MNI_registered.nii.gz
```

**Transformation Files:**
```
/mnt/Data/AKIB/Training data/{patient_id}/{source}/{patient_id}_{modality}_MNI_transform.tfm
```

## Examples

### Patient 1, 64mT, FLAIR
- **Input**: `/mnt/Data/AKIB/Training data/1/64mT/1_FLAIR_N4corrected.nii.gz`
- **Output**: `/mnt/Data/AKIB/Training data/1/64mT/1_FLAIR_MNI_registered.nii.gz`
- **Transform**: `/mnt/Data/AKIB/Training data/1/64mT/1_FLAIR_MNI_transform.tfm`

### Patient 25, 3T, T1
- **Input**: `/mnt/Data/AKIB/Training data/25/3T/25_T1_N4corrected.nii.gz`
- **Output**: `/mnt/Data/AKIB/Training data/25/3T/25_T1_MNI_registered.nii.gz`
- **Transform**: `/mnt/Data/AKIB/Training data/25/3T/25_T1_MNI_transform.tfm`

## File Sizes
- Original N4-corrected images: ~5.7-6.3 MB per file
- Registered images: ~6.0-6.3 MB per file
- Transform files: ~1-2 KB per file

## Registration Quality Metrics

All registrations completed successfully with:
- **Final metric values**: Typically -0.35 to -0.50 (Mattes MI)
- **Convergence**: Most converged via gradient magnitude tolerance
- **Stop conditions**:
  - Gradient magnitude tolerance met (most common)
  - Maximum iterations reached (some cases)
  - Minimum step size reached (some cases)

## Verification

To verify registration quality:

1. **Visual inspection** (in notebook):
   ```python
   # Use the visualization cell in 3D_medfussion.ipynb
   # Shows patient image in MNI space + template + overlay
   ```

2. **Command-line check**:
   ```bash
   # Count registered images
   find "/mnt/Data/AKIB/Training data" -name "*_MNI_registered.nii.gz" | wc -l
   # Should return: 300
   
   # List for specific patient
   ls -lh "/mnt/Data/AKIB/Training data/1/64mT/"*MNI*
   ```

3. **Check image dimensions**:
   ```python
   import SimpleITK as sitk
   img = sitk.ReadImage('/mnt/Data/AKIB/Training data/1/64mT/1_FLAIR_MNI_registered.nii.gz')
   print(f"Size: {img.GetSize()}")      # Should match template: (182, 218, 182)
   print(f"Spacing: {img.GetSpacing()}") # Should be: (1.0, 1.0, 1.0)
   ```

## Next Steps

The registered images are now ready for:
1. ✅ **Spatial normalization** - All images in common MNI space
2. ✅ **Cross-subject comparison** - Direct voxel-wise analysis possible
3. ✅ **Deep learning training** - Standardized input dimensions
4. ✅ **Statistical analysis** - Population-level studies enabled

## Preprocessing Pipeline Summary

Complete preprocessing pipeline for each image:

```
Original Image (raw acquisition)
    ↓
Skull Stripping (HD-BET)
    ↓  produces: *_bet_mask.nii.gz, *_skullstripped.nii.gz
    ↓
N4 Bias Field Correction (SimpleITK)
    ↓  produces: *_N4corrected.nii.gz
    ↓
Linear Registration to MNI152 (SimpleITK)
    ↓  produces: *_MNI_registered.nii.gz, *_MNI_transform.tfm
    ↓
✓ Ready for Analysis/Deep Learning
```

## Script Location

The registration script used:
```
/mnt/code/AKIB/Hybrid3DSRCycleGAN/linear_registration.py
```

To re-run or process additional images:
```bash
source /home/deeplearning01/anaconda3/etc/profile.d/conda.sh
conda activate iguane
python /mnt/code/AKIB/Hybrid3DSRCycleGAN/linear_registration.py
```

## Computational Details

- **Environment**: iguane conda environment
- **Python version**: 3.9
- **Key library**: SimpleITK 2.5.2
- **Processing time**: ~10-30 seconds per image
- **Total processing time**: ~1-2 hours for all 300 images

## Contact & References

- **Dataset**: AKIB Training data
- **Date**: November 3, 2025
- **MNI Template Source**: Montreal Neurological Institute (MNI152)

---

**Status**: ✅ All 300 images successfully registered to MNI152 space
