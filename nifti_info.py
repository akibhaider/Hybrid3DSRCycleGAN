import nibabel as nib
import numpy as np
from pathlib import Path


def get_nifti_info(file_path):
    """
    Get comprehensive information about a NIfTI MRI image.
    
    Args:
        file_path: Path to the NIfTI file (.nii or .nii.gz)
    
    Returns:
        dict: Dictionary containing image information
    """
    try:
        # Load the NIfTI file
        img = nib.load(str(file_path))
        
        # Get the image data
        data = img.get_fdata()
        
        # Get header information
        header = img.header
        
        # Compile information
        info = {
            # File information
            'file_path': str(file_path),
            'file_size_mb': Path(file_path).stat().st_size / (1024 * 1024),
            
            # Shape and dimensions
            'shape': data.shape,
            'ndim': data.ndim,
            'dimensions': {
                'width': data.shape[0],
                'height': data.shape[1],
                'depth': data.shape[2] if data.ndim >= 3 else None,
                'time': data.shape[3] if data.ndim >= 4 else None,
            },
            
            # Voxel information
            'voxel_size': header.get_zooms(),
            'voxel_volume_mm3': np.prod(header.get_zooms()[:3]) if len(header.get_zooms()) >= 3 else None,
            
            # Intensity information
            'data_type': str(data.dtype),
            'min_intensity': float(np.min(data)),
            'max_intensity': float(np.max(data)),
            'mean_intensity': float(np.mean(data)),
            'std_intensity': float(np.std(data)),
            'median_intensity': float(np.median(data)),
            
            # Non-zero voxel statistics (useful for brain images)
            'num_nonzero_voxels': int(np.count_nonzero(data)),
            'num_total_voxels': int(data.size),
            'percent_nonzero': float(100 * np.count_nonzero(data) / data.size),
            
            # Orientation information
            'affine': img.affine.tolist(),
            'orientation': nib.aff2axcodes(img.affine),
            
            # Header metadata
            'qform_code': int(header['qform_code']),
            'sform_code': int(header['sform_code']),
            'xyzt_units': str(header.get_xyzt_units()),
            
            # Description from header
            'description': str(header.get('descrip', b'')).strip() if header.get('descrip') is not None else '',
        }
        
        return info
        
    except Exception as e:
        return {'error': str(e), 'file_path': str(file_path)}


def print_nifti_info(file_path, verbose=True):
    """
    Print comprehensive information about a NIfTI MRI image in a readable format.
    
    Args:
        file_path: Path to the NIfTI file (.nii or .nii.gz)
        verbose: If True, print all details. If False, print summary only.
    """
    info = get_nifti_info(file_path)
    
    if 'error' in info:
        print(f"❌ Error loading file: {info['error']}")
        return info
    
    print(f"\n{'='*80}")
    print(f"📊 NIfTI Image Information")
    print(f"{'='*80}")
    
    # File information
    print(f"\n📁 File Information:")
    print(f"   Path: {info['file_path']}")
    print(f"   Size: {info['file_size_mb']:.2f} MB")
    
    # Dimensions
    print(f"\n📐 Dimensions:")
    print(f"   Shape: {info['shape']}")
    print(f"   Number of dimensions: {info['ndim']}")
    print(f"   Width (X):  {info['dimensions']['width']} voxels")
    print(f"   Height (Y): {info['dimensions']['height']} voxels")
    if info['dimensions']['depth']:
        print(f"   Depth (Z):  {info['dimensions']['depth']} voxels")
    if info['dimensions']['time']:
        print(f"   Time:       {info['dimensions']['time']} volumes")
    
    # Voxel information
    print(f"\n🔬 Voxel Information:")
    voxel_size = info['voxel_size']
    print(f"   Voxel size: {voxel_size[0]:.4f} × {voxel_size[1]:.4f} × {voxel_size[2]:.4f} mm")
    if info['voxel_volume_mm3']:
        print(f"   Voxel volume: {info['voxel_volume_mm3']:.6f} mm³")
    
    # Intensity statistics
    print(f"\n💡 Intensity Statistics:")
    print(f"   Data type: {info['data_type']}")
    print(f"   Min:       {info['min_intensity']:.4f}")
    print(f"   Max:       {info['max_intensity']:.4f}")
    print(f"   Mean:      {info['mean_intensity']:.4f}")
    print(f"   Std Dev:   {info['std_intensity']:.4f}")
    print(f"   Median:    {info['median_intensity']:.4f}")
    
    # Non-zero voxels
    print(f"\n🧠 Non-Zero Voxel Statistics:")
    print(f"   Total voxels:    {info['num_total_voxels']:,}")
    print(f"   Non-zero voxels: {info['num_nonzero_voxels']:,} ({info['percent_nonzero']:.2f}%)")
    
    # Orientation
    print(f"\n🧭 Orientation:")
    print(f"   Axes orientation: {info['orientation']}")
    
    if verbose:
        print(f"\n📋 Header Metadata:")
        print(f"   QForm code: {info['qform_code']}")
        print(f"   SForm code: {info['sform_code']}")
        print(f"   XYZT units: {info['xyzt_units']}")
        if info['description']:
            print(f"   Description: {info['description']}")
        
        print(f"\n🔢 Affine Matrix:")
        affine = np.array(info['affine'])
        for row in affine:
            print(f"   {row}")
    
    print(f"\n{'='*80}\n")
    
    return info


def compare_nifti_images(file_path1, file_path2):
    """
    Compare two NIfTI images and highlight differences.
    
    Args:
        file_path1: Path to first NIfTI file
        file_path2: Path to second NIfTI file
    """
    print(f"\n{'='*80}")
    print(f"🔍 Comparing NIfTI Images")
    print(f"{'='*80}")
    
    info1 = get_nifti_info(file_path1)
    info2 = get_nifti_info(file_path2)
    
    if 'error' in info1 or 'error' in info2:
        print("❌ Error loading one or both files")
        return
    
    # Compare key attributes
    print(f"\n📁 File 1: {Path(file_path1).name}")
    print(f"📁 File 2: {Path(file_path2).name}\n")
    
    comparisons = [
        ('Shape', 'shape'),
        ('Voxel size', 'voxel_size'),
        ('Data type', 'data_type'),
        ('Orientation', 'orientation'),
        ('File size (MB)', 'file_size_mb'),
        ('Min intensity', 'min_intensity'),
        ('Max intensity', 'max_intensity'),
        ('Mean intensity', 'mean_intensity'),
    ]
    
    for label, key in comparisons:
        val1 = info1[key]
        val2 = info2[key]
        match = "✅" if val1 == val2 else "❌"
        print(f"{match} {label}:")
        print(f"   File 1: {val1}")
        print(f"   File 2: {val2}")
        print()
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print_nifti_info(file_path, verbose=True)
    else:
        # Test with example files
        test_files = [
            "/mnt/Data/AKIB/Training data/13/3T/13_T2.nii.gz",
            "/mnt/Data/AKIB/Training data/13/3T/13_T2_bet_mask.nii.gz",
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                print_nifti_info(test_file, verbose=False)
