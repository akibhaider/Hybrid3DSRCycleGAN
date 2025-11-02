import os
from pathlib import Path
from HD_BET.run import run_hd_bet as hd_bet_run
import torch
import time
from datetime import datetime

def run_hd_bet(input_file: Path, output_file: Path, mode: str = 'accurate', device: int = 0):
    """
    Executes the HD-BET Python API for skull stripping.
    
    Args:
        input_file: Path object for the NIfTI input file.
        output_file: Path object for the NIfTI output file.
        mode: HD-BET mode ('fast' or 'accurate'). 'accurate' is recommended.
        device: GPU device number (0, 1, etc.) or 'cpu' for CPU processing.
    """
    try:
        # HD-BET expects lists for batch processing
        input_files = [str(input_file)]
        output_files = [str(output_file)]
        
        # Run HD-BET using the Python API
        hd_bet_run(
            mri_fnames=input_files,
            output_fnames=output_files,
            mode=mode,
            device=device,
            postprocess=False,
            do_tta=True,  # Test-time augmentation for better results
            keep_mask=True,  # Keep the brain mask
            overwrite=True
        )
        print(f"      ✅ Success: {output_file.name}")
        return True
    except Exception as e:
        print(f"      ❌ Error: {str(e)}")
        return False


def get_all_files_to_process(base_dir: Path):
    """Scan and return all files that need processing."""
    files_to_process = []
    modalities = ['T1', 'T2', 'FLAIR']
    sites = ['3T', '64mT']
    
    for patient_id in range(1, 51):
        patient_dir = base_dir / str(patient_id)
        if not patient_dir.is_dir():
            continue
        
        for site in sites:
            site_dir = patient_dir / site
            if not site_dir.is_dir():
                continue
            
            for modality in modalities:
                input_file = site_dir / f"{patient_id}_{modality}.nii.gz"
                output_file = site_dir / f"{patient_id}_{modality}_bet.nii.gz"
                
                if input_file.exists() and not output_file.exists():
                    files_to_process.append({
                        'input': input_file,
                        'output': output_file,
                        'patient': patient_id,
                        'site': site,
                        'modality': modality
                    })
    
    return files_to_process


def process_all_data():
    """Process all patient data for skull stripping using HD-BET."""
    
    # Define the base directory where your training data is stored
    BASE_DIR = Path('/mnt/Data/AKIB/Training data')

    if not BASE_DIR.is_dir():
        print(f"❌ Error: Base directory not found at {BASE_DIR}")
        return

    # GPU Configuration - Force use of CUDA core 1
    if not torch.cuda.is_available():
        print("❌ Error: CUDA is not available. GPU processing cannot proceed.")
        return
    
    # Set CUDA device to GPU 1
    gpu_device = 1
    if torch.cuda.device_count() < gpu_device + 1:
        print(f"⚠️  Warning: GPU {gpu_device} not available. Using GPU 0 instead.")
        gpu_device = 0
    
    # Set the device
    torch.cuda.set_device(gpu_device)
    
    # Display GPU information
    print(f"\n{'='*80}")
    print(f"🚀 HD-BET Skull Stripping Pipeline - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"📊 GPU Configuration:")
    print(f"   - Total GPUs available: {torch.cuda.device_count()}")
    print(f"   - Using GPU: {gpu_device}")
    print(f"   - GPU Name: {torch.cuda.get_device_name(gpu_device)}")
    print(f"   - GPU Memory: {torch.cuda.get_device_properties(gpu_device).total_memory / 1e9:.2f} GB")
    print(f"{'='*80}\n")

    # Scan all files that need processing
    print("🔍 Scanning for files to process...")
    files_to_process = get_all_files_to_process(BASE_DIR)
    total_files = len(files_to_process)
    
    if total_files == 0:
        print("✨ All files have already been processed!")
        return
    
    print(f"📁 Found {total_files} files to process\n")
    print(f"{'='*80}\n")

    # Track processing statistics
    total_processed = 0
    total_errors = 0
    start_time = time.time()
    file_times = []

    # Process each file
    for idx, file_info in enumerate(files_to_process, 1):
        file_start = time.time()
        
        # Progress header
        progress_pct = (idx / total_files) * 100
        elapsed = time.time() - start_time
        
        if idx > 1:
            avg_time = sum(file_times) / len(file_times)
            remaining_files = total_files - idx + 1
            eta_seconds = avg_time * remaining_files
            eta_min = int(eta_seconds // 60)
            eta_sec = int(eta_seconds % 60)
            eta_str = f"ETA: {eta_min}m {eta_sec}s"
        else:
            eta_str = "ETA: Calculating..."
        
        print(f"{'─'*80}")
        print(f"[{idx}/{total_files}] ({progress_pct:.1f}%) | {eta_str}")
        print(f"    📄 Patient {file_info['patient']} | Site: {file_info['site']} | Modality: {file_info['modality']}")
        print(f"    🔄 Processing: {file_info['input'].name}")
        
        # Process the file
        success = run_hd_bet(
            file_info['input'], 
            file_info['output'], 
            mode='accurate', 
            device=gpu_device
        )
        
        file_time = time.time() - file_start
        file_times.append(file_time)
        
        if success:
            total_processed += 1
            print(f"    ⏱️  Time: {file_time:.2f}s")
        else:
            total_errors += 1
        
        print()

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Print summary
    print(f"\n{'='*80}")
    print(f"✨ Skull Stripping Pipeline Complete - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"📊 Summary:")
    print(f"   - Total processed successfully: {total_processed}")
    print(f"   - Total errors: {total_errors}")
    print(f"   - Total time: {int(hours)}h {int(minutes)}m {int(seconds)}s")
    if total_processed > 0:
        avg_time = sum(file_times) / len(file_times)
        print(f"   - Average time per file: {avg_time:.2f}s")
        print(f"   - Min time: {min(file_times):.2f}s")
        print(f"   - Max time: {max(file_times):.2f}s")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Set environment variable to use specific GPU (optional, for additional control)
    os.environ['CUDA_VISIBLE_DEVICES'] = '1'
    
    # Run the processing pipeline
    process_all_data()