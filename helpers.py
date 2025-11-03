import matplotlib.pyplot as plt

from ipywidgets import interact
import numpy as np
import SimpleITK as sitk
import cv2
import nibabel as nib
from pathlib import Path

def explore_3D_array(arr: np.ndarray, cmap: str = 'gray'):
  """
  Given a 3D array with shape (Z,X,Y) This function will create an interactive
  widget to check out all the 2D arrays with shape (X,Y) inside the 3D array. 
  The purpose of this function to visual inspect the 2D arrays in the image. 

  Args:
    arr : 3D array with shape (Z,X,Y) that represents the volume of a MRI image
    cmap : Which color map use to plot the slices in matplotlib.pyplot
  """

  def fn(SLICE):
    plt.figure(figsize=(7,7))
    plt.imshow(arr[SLICE, :, :], cmap=cmap)
    plt.show()

  interact(fn, SLICE=(0, arr.shape[0]-1))


def explore_3D_array_comparison(arr_before: np.ndarray, arr_after: np.ndarray, cmap: str = 'gray'):
  """
  Given two 3D arrays with shape (Z,X,Y) This function will create an interactive
  widget to check out all the 2D arrays with shape (X,Y) inside the 3D arrays.
  The purpose of this function to visual compare the 2D arrays after some transformation. 

  Args:
    arr_before : 3D array with shape (Z,X,Y) that represents the volume of a MRI image, before any transform
    arr_after : 3D array with shape (Z,X,Y) that represents the volume of a MRI image, after some transform    
    cmap : Which color map use to plot the slices in matplotlib.pyplot
  """

  assert arr_after.shape == arr_before.shape

  def fn(SLICE):
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex='col', sharey='row', figsize=(10,10))

    ax1.set_title('Before', fontsize=15)
    ax1.imshow(arr_before[SLICE, :, :], cmap=cmap)

    ax2.set_title('After', fontsize=15)
    ax2.imshow(arr_after[SLICE, :, :], cmap=cmap)

    plt.tight_layout()
    plt.show()
  
  interact(fn, SLICE=(0, arr_before.shape[0]-1))


def show_sitk_img_info(img: sitk.Image):
  """
  Given a sitk.Image instance prints the information about the MRI image contained.

  Args:
    img : instance of the sitk.Image to check out
  """
  pixel_type = img.GetPixelIDTypeAsString()
  origin = img.GetOrigin()
  dimensions = img.GetSize()
  spacing = img.GetSpacing()
  direction = img.GetDirection()

  info = {'Pixel Type' : pixel_type, 'Dimensions': dimensions, 'Spacing': spacing, 'Origin': origin,  'Direction' : direction}
  for k,v in info.items():
    print(f' {k} : {v}')


def add_suffix_to_filename(filename: str, suffix:str) -> str:
  """
  Takes a NIfTI filename and appends a suffix.

  Args:
      filename : NIfTI filename
      suffix : suffix to append

  Returns:
      str : filename after append the suffix
  """
  if filename.endswith('.nii'):
      result = filename.replace('.nii', f'_{suffix}.nii')
      return result
  elif filename.endswith('.nii.gz'):
      result = filename.replace('.nii.gz', f'_{suffix}.nii.gz')
      return result
  else:
      raise RuntimeError('filename with unknown extension')


def rescale_linear(array: np.ndarray, new_min: int, new_max: int):
  """Rescale an array linearly."""
  minimum, maximum = np.min(array), np.max(array)
  m = (new_max - new_min) / (maximum - minimum)
  b = new_min - m * minimum
  return m * array + b


def explore_3D_array_with_mask_contour(arr: np.ndarray, mask: np.ndarray, thickness: int = 1):
  """
  Given a 3D array with shape (Z,X,Y) This function will create an interactive
  widget to check out all the 2D arrays with shape (X,Y) inside the 3D array. The binary
  mask provided will be used to overlay contours of the region of interest over the 
  array. The purpose of this function is to visual inspect the region delimited by the mask.

  Args:
    arr : 3D array with shape (Z,X,Y) that represents the volume of a MRI image
    mask : binary mask to obtain the region of interest
  """
  assert arr.shape == mask.shape
  
  _arr = rescale_linear(arr,0,1)
  _mask = rescale_linear(mask,0,1)
  _mask = _mask.astype(np.uint8)

  def fn(SLICE):
    arr_rgb = cv2.cvtColor(_arr[SLICE, :, :], cv2.COLOR_GRAY2RGB)
    contours, _ = cv2.findContours(_mask[SLICE, :, :], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    arr_with_contours = cv2.drawContours(arr_rgb, contours, -1, (0,1,0), thickness)

    plt.figure(figsize=(7,7))
    plt.imshow(arr_with_contours)
    plt.show()

  interact(fn, SLICE=(0, arr.shape[0]-1))


def get_nifti_info(file_path):
  """
  Get comprehensive information about a NIfTI MRI image.
  
  Args:
      file_path: Path to the NIfTI file (.nii or .nii.gz)
  
  Returns:
      dict: Dictionary containing image information including:
          - shape, dimensions (width, height, depth)
          - voxel size and volume
          - intensity statistics (min, max, mean, std, median)
          - non-zero voxel counts
          - orientation and affine matrix
          - header metadata
  
  Example:
      >>> info = get_nifti_info('/path/to/image.nii.gz')
      >>> print(f"Shape: {info['shape']}")
      >>> print(f"Voxel size: {info['voxel_size']}")
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
      }
      
      return info
      
  except Exception as e:
      return {'error': str(e), 'file_path': str(file_path)}


def print_nifti_info(file_path):
  """
  Print comprehensive information about a NIfTI MRI image in a readable format.
  
  Args:
      file_path: Path to the NIfTI file (.nii or .nii.gz)
  
  Returns:
      dict: Dictionary containing the image information
  
  Example:
      >>> print_nifti_info('/path/to/image.nii.gz')
  """
  info = get_nifti_info(file_path)
  
  if 'error' in info:
      print(f"❌ Error loading file: {info['error']}")
      return info
  
  print(f"\n{'='*70}")
  print(f"📊 NIfTI Image Information")
  print(f"{'='*70}")
  
  # File information
  print(f"\n📁 File: {Path(info['file_path']).name}")
  print(f"   Size: {info['file_size_mb']:.2f} MB")
  
  # Dimensions
  print(f"\n📐 Dimensions:")
  print(f"   Shape: {info['shape']}")
  print(f"   Width (X):  {info['dimensions']['width']} voxels")
  print(f"   Height (Y): {info['dimensions']['height']} voxels")
  if info['dimensions']['depth']:
      print(f"   Depth (Z):  {info['dimensions']['depth']} voxels")
  
  # Voxel information
  print(f"\n🔬 Voxel Information:")
  voxel_size = info['voxel_size']
  print(f"   Voxel size: {voxel_size[0]:.4f} × {voxel_size[1]:.4f} × {voxel_size[2]:.4f} mm")
  if info['voxel_volume_mm3']:
      print(f"   Voxel volume: {info['voxel_volume_mm3']:.6f} mm³")
  
  # Intensity statistics
  print(f"\n💡 Intensity Statistics:")
  print(f"   Data type: {info['data_type']}")
  print(f"   Min:    {info['min_intensity']:.4f}")
  print(f"   Max:    {info['max_intensity']:.4f}")
  print(f"   Mean:   {info['mean_intensity']:.4f}")
  print(f"   Std:    {info['std_intensity']:.4f}")
  print(f"   Median: {info['median_intensity']:.4f}")
  
  # Non-zero voxels
  print(f"\n🧠 Coverage:")
  print(f"   Total voxels:    {info['num_total_voxels']:,}")
  print(f"   Non-zero voxels: {info['num_nonzero_voxels']:,} ({info['percent_nonzero']:.2f}%)")
  
  # Orientation
  print(f"\n🧭 Orientation: {info['orientation']}")
  
  print(f"\n{'='*70}\n")
  
  return info
