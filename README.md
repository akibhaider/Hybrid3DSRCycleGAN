# Hybrid 3D Super-Resolution CycleGAN for MRI Enhancement

## 🧠 Project Overview

This project implements a comprehensive preprocessing and analysis pipeline for multi-modal MRI data, preparing datasets for a Hybrid 3D Super-Resolution CycleGAN. The pipeline processes T1, T2, and FLAIR MRI sequences from both 64mT (low-field) and 3T (high-field) scanners.

## 📊 Dataset Information

- **50 Patients** with multi-modal MRI scans
- **2 Scanner Types**: 64mT (low-field) and 3T (high-field)
- **3 Modalities per patient**: T1, T2, FLAIR
- **Total Images**: 300 (50 patients × 2 sources × 3 modalities)

## 🔬 Preprocessing Pipeline

### Pipeline Stages (100% Complete)

```
Raw MRI Data
    ↓
1. Skull Stripping (HD-BET)           [✓ 300/300 images]
    ↓
2. N4 Bias Field Correction          [✓ 300/300 images]
    ↓
3. MNI Space Registration (Linear)    [✓ 300/300 images]
    ↓
4. Brain Extraction in MNI Space      [✓ 300/300 images]
    ↓
5. Non-linear Co-registration         [✓ 200/200 images]
   (T2/FLAIR → T1 alignment)
    ↓
Training-Ready Data
```

### Key Features

- **Standardized Space**: All images registered to MNI152 template (1mm³ isotropic)
- **Brain-Only Images**: Clean, skull-stripped data (~0.3-0.8 MB per file)
- **Multi-modal Alignment**: Perfect spatial correspondence between T1, T2, and FLAIR
- **Quality Control**: Interactive 3D visualization for each preprocessing stage

## 🛠️ Technologies Used

### Core Libraries
- **SimpleITK** 2.5.2: Medical image processing and registration
- **ANTsPy** 0.6.1: Advanced non-linear registration (SyN)
- **HD-BET**: Deep learning-based brain extraction
- **Nibabel**: NIfTI file I/O
- **PyTorch**: Deep learning framework

### Environment
- **Python**: 3.9
- **Conda Environment**: `iguane` (see `preproces_env.yml`)

## 📁 Repository Structure

```
Hybrid3DSRCycleGAN/
├── preprocessing/
│   ├── skull_strip_data.py              # HD-BET brain extraction
│   ├── bias_correction.py               # N4 bias field correction
│   ├── linear_registration.py           # MNI space registration
│   ├── mni_masking_simpleitk.py         # Brain masking in MNI space
│   └── non_linear_coregistration.py     # ANTs SyN co-registration
│
├── monitoring/
│   ├── monitor_bias_correction.sh       # Progress tracker
│   └── monitor_nonlinear_registration.sh
│
├── notebooks/
│   └── 3D_medfussion.ipynb              # Interactive visualization
│
├── docs/
│   ├── PREPROCESSING_COMPLETE_SUMMARY.md
│   ├── REGISTRATION_SUMMARY.md
│   └── MNI_MASKING_README.md
│
├── environment/
│   └── preproces_env.yml                # Conda environment
│
└── utils/
    ├── all_in_one.py                    # Unified preprocessing
    ├── data_augmentation.py
    ├── helpers.py
    └── nifti_info.py
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Create conda environment
conda env create -f preproces_env.yml
conda activate iguane
```

### 2. Run Preprocessing Pipeline

#### Step 1: Skull Stripping
```bash
python skull_strip_data.py
```

#### Step 2: Bias Field Correction
```bash
python bias_correction.py
```

#### Step 3: MNI Registration
```bash
python linear_registration.py
```

#### Step 4: Brain Extraction in MNI Space
```bash
python mni_masking_simpleitk.py
```

#### Step 5: Co-registration (Optional)
```bash
python non_linear_coregistration.py
```

### 3. Visualization

Open and run `3D_medfussion.ipynb` to visualize:
- Complete preprocessing pipeline (7 stages)
- 3D slice-by-slice comparison
- Original vs synthetic FLAIR comparison

## 📊 Preprocessing Results

### File Size Reduction
- **Original MRI**: ~20 MB
- **MNI Registered**: ~6 MB
- **MNI Brain (Final)**: ~0.3-0.8 MB

### Processing Time (on 24-core CPU)
- Skull stripping: ~30s per image
- N4 correction: ~45s per image
- MNI registration: ~60s per image
- Brain masking: <1s per image
- Co-registration: ~30s per pair

### Quality Metrics
- ✅ All images successfully preprocessed
- ✅ Zero failed registrations
- ✅ Spatial alignment verified visually
- ✅ Intensity normalization applied

## 🔍 Data Flow

### Input Files (per patient)
```
/mnt/Data/AKIB/Training data/{patient_id}/{source}/
├── {patient}_{modality}.nii.gz          # Original
```

### Output Files (per patient)
```
/mnt/Data/AKIB/Training data/{patient_id}/{source}/
├── {patient}_{modality}_bet_mask.nii.gz        # Brain mask
├── {patient}_{modality}_skullstripped.nii.gz   # Skull-stripped
├── {patient}_{modality}_N4corrected.nii.gz     # Bias corrected
├── {patient}_{modality}_MNI_registered.nii.gz  # MNI space
├── {patient}_{modality}_MNI_transform.tfm      # Transform
├── {patient}_{modality}_MNI_brain.nii.gz       # Final (brain-only in MNI)
└── {patient}_{T2/FLAIR}_to_T1_Warped.nii.gz   # Co-registered
```

## 🎯 Next Steps

### Model Training Preparation
1. **Intensity Normalization**
   - Z-score normalization
   - Percentile-based scaling
   - Min-max normalization

2. **Patch Extraction**
   - 3D patches (64×64×64 or 128×128×128)
   - Sliding window or random sampling
   - HDF5/numpy array storage

3. **Data Splitting**
   - Train/Validation/Test (70/15/15)
   - Stratified by scanner type

4. **PyTorch Dataset**
   - Custom Dataset class
   - DataLoader with batching
   - On-the-fly augmentation

### Model Architecture
- 3D U-Net generator
- CycleGAN discriminator
- Hybrid SR-CycleGAN framework
- Loss functions: MSE + Adversarial + Cycle-consistency

## 📈 Monitoring & Quality Control

### Real-time Progress Monitoring
```bash
# Monitor bias correction
bash monitor_bias_correction.sh

# Monitor co-registration
bash monitor_nonlinear_registration.sh
```

### Visual Quality Control
Use the Jupyter notebook (`3D_medfussion.ipynb`) for:
- Interactive 3D slice browsing
- Side-by-side comparison of preprocessing stages
- Intensity distribution analysis
- Spatial alignment verification

## 🤝 Contributing

This project is part of ongoing research in medical image super-resolution and domain adaptation for low-field MRI enhancement.

## 📝 Citation

If you use this preprocessing pipeline or code, please cite:

```bibtex
@misc{hybrid3dsrcyclegan2025,
  author = {Akib Haider},
  title = {Hybrid 3D Super-Resolution CycleGAN for MRI Enhancement},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/akibhaider/Hybrid3DSRCycleGAN}
}
```

## 📧 Contact

- **Author**: Akib Haider
- **GitHub**: [@akibhaider](https://github.com/akibhaider)
- **Project**: Hybrid3DSRCycleGAN

## 📜 License

[Add your license here]

## 🙏 Acknowledgments

- HD-BET for robust brain extraction
- SimpleITK for medical image processing
- ANTs for advanced registration algorithms
- MNI template for standardized brain space

---

**Status**: Preprocessing Complete ✅ | Ready for Model Training 🚀
