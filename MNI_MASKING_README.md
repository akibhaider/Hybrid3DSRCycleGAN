# MNI Masking and Brain Isolation Pipeline

## Overview
This script applies final brain masking to MNI-registered full-head images to produce clean, brain-extracted MRI volumes in standard MNI space.

## Prerequisites

### Required Software
1. **FSL (FMRIB Software Library)**
   - `flirt` - for applying transformations
   - `fslmaths` - for image arithmetic operations
   
2. **Convert3D (c3d)**
   - `c3d_affine_tool` - for converting SimpleITK transforms to FSL format

### Input Requirements
- FLAIR brain mask: `{patient}_{source}/FLAIR_bet_mask.nii.gz`
- MNI-registered full-head images: `{patient}_{modality}_MNI_registered_fullhead.nii.gz`
- SimpleITK transform files: `{patient}_{modality}_MNI_fullhead_transform.tfm`

## Pipeline Steps

### Step 4a: Transform Conversion
**Purpose**: Convert SimpleITK `.tfm` format to FSL `.mat` format

**Input**: 
- `{patient}_{modality}_MNI_fullhead_transform.tfm`

**Command**:
```bash
c3d_affine_tool \
  -ref MNI152_T1_1mm.nii.gz \
  -src {patient}_{modality}_MNI_registered_fullhead.nii.gz \
  {patient}_{modality}_MNI_fullhead_transform.tfm \
  -fsl {patient}_{modality}_MNI_fullhead.mat \
  -oitk {patient}_{modality}_MNI_fullhead_transform.tfm
```

**Output**: 
- `{patient}_{modality}_MNI_fullhead.mat` (FSL-compatible transformation matrix)

---

### Step 4b: Mask Transformation
**Purpose**: Apply the MNI transformation to the original brain mask

**Input**:
- Original mask: `{patient}_FLAIR_bet_mask.nii.gz`
- FSL matrix: `{patient}_{modality}_MNI_fullhead.mat`
- Reference template: `MNI152_T1_1mm.nii.gz`

**Command**:
```bash
flirt -applyxfm \
  -in {patient}_FLAIR_bet_mask.nii.gz \
  -ref MNI152_T1_1mm.nii.gz \
  -out {patient}_{modality}_MNI_mask.nii.gz \
  -init {patient}_{modality}_MNI_fullhead.mat \
  -interp nearestneighbour
```

**Key Parameters**:
- `-applyxfm`: Apply existing transformation (no re-registration)
- `-interp nearestneighbour`: Preserves binary mask values (0 or 1)

**Output**: 
- `{patient}_{modality}_MNI_mask.nii.gz` (mask in MNI space)

---

### Step 4c: Final Brain Isolation
**Purpose**: Apply the transformed mask to isolate brain tissue

**Input**:
- Registered full-head: `{patient}_{modality}_MNI_registered_fullhead.nii.gz`
- Warped mask: `{patient}_{modality}_MNI_mask.nii.gz`

**Command**:
```bash
fslmaths \
  {patient}_{modality}_MNI_registered_fullhead.nii.gz \
  -mul {patient}_{modality}_MNI_mask.nii.gz \
  {patient}_{modality}_FINAL_MNI.nii.gz
```

**Operation**: Element-wise multiplication (voxels outside mask → 0)

**Output**: 
- `{patient}_{modality}_FINAL_MNI.nii.gz` ⭐ **FINAL STANDARDIZED BRAIN**

---

## Data Flow Summary

```
Original Mask          Transform (SimpleITK)     Registered Full-Head
    ↓                         ↓                          ↓
{patient}_FLAIR_     {patient}_{mod}_          {patient}_{mod}_
bet_mask.nii.gz      MNI_fullhead_             MNI_registered_
                     transform.tfm              fullhead.nii.gz
    ↓                         ↓
    ↓                   [Convert to FSL]
    ↓                         ↓
    ↓                  {patient}_{mod}_
    ↓                  MNI_fullhead.mat
    ↓                         ↓
    └──────[Apply Transform]──┘
                ↓
         {patient}_{mod}_
         MNI_mask.nii.gz
                ↓
    [Multiply with Full-Head]
                ↓
    ★ {patient}_{mod}_FINAL_MNI.nii.gz ★
```

---

## Configuration

### Dataset Structure
- **Patients**: 1-50
- **Sources**: 3T, 64mT
- **Modalities**: T1, T2, FLAIR

### File Naming Convention
- Mask: `{patient}_FLAIR_bet_mask.nii.gz`
- Transform: `{patient}_{modality}_MNI_fullhead_transform.tfm`
- Registered: `{patient}_{modality}_MNI_registered_fullhead.nii.gz`
- **Final output**: `{patient}_{modality}_FINAL_MNI.nii.gz`

---

## Expected Outputs

### Per Patient/Source/Modality
For each combination (e.g., Patient 1, 3T, T1):
1. `1_T1_MNI_fullhead.mat` - FSL transformation matrix
2. `1_T1_MNI_mask.nii.gz` - Warped brain mask
3. `1_T1_FINAL_MNI.nii.gz` ⭐ - **Final brain-extracted MNI image**

### Total Files
- **Per patient/source**: 3 modalities × 3 files = 9 files
- **Total**: 50 patients × 2 sources × 9 files = **900 new files**
- **Final outputs**: 50 × 2 × 3 = **300 FINAL_MNI.nii.gz files**

---

## Usage

### Run the Script
```bash
# Activate environment (if using conda)
conda activate iguane

# Execute the masking pipeline
python mni_masking_and_brain_isolation.py
```

### Monitor Progress
The script will print:
- Patient/source/modality being processed
- Success/failure of each step
- Final output file paths

### Verify Outputs
```bash
# Count final outputs
find '/mnt/Data/AKIB/Training data' -name '*_FINAL_MNI.nii.gz' | wc -l
# Expected: 300

# Check one example
ls -lh "/mnt/Data/AKIB/Training data/1/3T/" | grep FINAL_MNI
```

---

## Key Differences from Previous Steps

| Aspect | Step 3 (Registration) | Step 4 (This Script) |
|--------|----------------------|---------------------|
| **Input** | N4-corrected full-head | Registered full-head + mask |
| **Output** | MNI-registered full-head | Brain-only MNI |
| **Skull** | Included | Removed |
| **Purpose** | Spatial normalization | Clean brain extraction |
| **File suffix** | `_MNI_registered_fullhead.nii.gz` | `_FINAL_MNI.nii.gz` |

---

## Troubleshooting

### "Required binary not found"
- **Issue**: FSL or c3d_affine_tool not in PATH
- **Solution**: 
  ```bash
  # Check FSL installation
  which flirt
  
  # Check c3d installation
  which c3d_affine_tool
  
  # Add to PATH if needed
  export PATH="/usr/local/fsl/bin:$PATH"
  export PATH="/usr/local/c3d/bin:$PATH"
  ```

### "FLAIR Brain Mask not found"
- **Issue**: Missing HD-BET mask from skull-stripping step
- **Solution**: Ensure skull-stripping (Step 1) was completed successfully

### "Step 3 output missing"
- **Issue**: Missing MNI registration files
- **Solution**: Run `linear_registration.py` first to create `_MNI_registered_fullhead.nii.gz` files

### Transform conversion fails
- **Issue**: c3d_affine_tool incompatible with transform
- **Solution**: Verify SimpleITK transform format is correct (should be Euler3DTransform)

---

## Next Steps

After completing this masking step:

1. **Quality Control**: Visualize final outputs in FSLeyes or notebook
2. **Intensity Normalization**: Apply z-score or percentile normalization
3. **Patch Extraction**: Create training patches for deep learning
4. **Data Loading**: Set up PyTorch/TensorFlow datasets
5. **Model Training**: Begin 3D Super-Resolution CycleGAN training

---

## Notes

- **Mask source**: Uses FLAIR mask for all modalities (FLAIR typically has best brain contrast)
- **Interpolation**: Nearest neighbor for masks preserves binary values
- **Element-wise multiplication**: `fslmaths -mul` sets non-brain voxels to 0
- **No data loss**: Original files remain unchanged; new files created
- **Idempotent**: Can be re-run safely; will recreate outputs

---

## File Size Expectations

- FSL matrix (`.mat`): ~1 KB (text file with 4×4 matrix)
- MNI mask: ~1-2 MB (binary mask in MNI space)
- **Final MNI brain**: ~3-6 MB (brain-only, standard space)

Compare to:
- Registered full-head: ~6-8 MB
- Original full-head: ~20 MB

---

## Author Notes
Created: November 3, 2025
Purpose: Final step in preprocessing pipeline for Hybrid 3D SR-CycleGAN project
Dependencies: FSL, Convert3D (c3d), SimpleITK
