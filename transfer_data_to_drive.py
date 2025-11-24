"""
Script to transfer collected radar data from Windows to Google Drive folder structure.

This script:
1. Finds .bin files collected by click_gui_continuous.py
2. Copies them to the proper MITO folder structure in Google Drive
3. Creates/updates metadata JSON files

Usage:
    # On Windows (after collecting data):
    python transfer_data_to_drive.py --source "C:\\ti\\mmwave_studio_02_01_01_00\\mmWaveStudio\\PostProc\\Data" --obj_id 000 --obj_name test_object

    # Or use default source location:
    python transfer_data_to_drive.py --obj_id 001 --obj_name my_object --exp_num 1
"""

import os
import shutil
import json
import argparse
from datetime import datetime
from pathlib import Path

def find_bin_files(source_dir, timestamp=None):
    """
    Find .bin files in the source directory.
    
    Args:
        source_dir: Directory containing adc_data_*.bin files
        timestamp: Optional specific timestamp to look for
    
    Returns:
        List of (timestamp, filepath) tuples
    """
    bin_files = []
    for filename in os.listdir(source_dir):
        if filename.startswith('adc_data_') and filename.endswith('_Raw_0.bin'):
            # Extract timestamp from filename: adc_data_{timestamp}_Raw_0.bin
            ts_str = filename.replace('adc_data_', '').replace('_Raw_0.bin', '')
            try:
                ts = int(ts_str)
                if timestamp is None or ts == timestamp:
                    bin_files.append((ts, os.path.join(source_dir, filename)))
            except ValueError:
                print(f"Warning: Could not parse timestamp from {filename}")
    
    return sorted(bin_files, key=lambda x: x[0])

def create_metadata_file(bin_filepath, output_dir, timestamp, params):
    """
    Create a metadata JSON file matching the .bin file.
    
    Args:
        bin_filepath: Path to the .bin file
        output_dir: Directory to save metadata
        timestamp: Timestamp for the file
        params: Radar parameters dictionary
    """
    # Get file creation and modification times
    ctime = os.path.getctime(bin_filepath)
    mtime = os.path.getmtime(bin_filepath)
    
    # Create metadata
    metadata = {
        "timestamp_compact": timestamp,
        "capture_start_time": ctime,
        "datetime_strftime": datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S"),
        "num_frames": params['num_frames'],
        "num_samples": params['num_samples'],
        "num_chirps": params['num_chirps'],
        "num_rx": params['num_rx'],
        "num_tx": params['num_tx'],
        "sweep_time": params.get('sweep_time', 0.001),
        "periodicity": params.get('periodicity', 0.01),
        "start_freq_ghz": params.get('start_freq', 77.5),
        "end_freq_ghz": params.get('end_freq', 80.5),
        "slope_hz_per_sample": params.get('slope', 6001200),
        "sample_rate_ksps": params.get('sample_rate', 10000),
        "source_file": os.path.basename(bin_filepath),
        "file_size_bytes": os.path.getsize(bin_filepath)
    }
    
    # Save metadata
    metadata_filename = f"metadata_{timestamp}.json"
    metadata_path = os.path.join(output_dir, metadata_filename)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)
    
    print(f"  Created metadata: {metadata_filename}")
    return metadata_path

def get_radar_params(config_file=None):
    """
    Get radar parameters from config or use defaults.
    
    Args:
        config_file: Optional path to params.json or config file
    
    Returns:
        Dictionary of radar parameters
    """
    default_params = {
        'num_frames': 4000,  # From DataCaptureDemo_xWR_cli_continuous.lua
        'num_samples': 512,
        'num_chirps': 1,     # Single chirp per frame
        'num_rx': 4,         # IWR1443: 4 RX antennas
        'num_tx': 3,         # IWR1443: 3 TX antennas (but only 1 enabled)
        'sweep_time': 0.00006,  # 60 microseconds ramp time
        'periodicity': 0.003,   # 3 ms frame periodicity
        'start_freq': 77.5,
        'end_freq': 80.5,
        'slope': 6001200,    # Hz per sample
        'sample_rate': 10000 # 10 MHz
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                if 'iwr1443' in config:
                    default_params.update(config['iwr1443'].get('current', {}))
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    return default_params

def transfer_data(source_dir, dest_base, obj_id, obj_name, x_angle=0, y_angle=0, z_angle=0, 
                  exp_num=1, is_los=True, timestamp=None, params=None, dry_run=False):
    """
    Transfer .bin files to MITO folder structure.
    
    Args:
        source_dir: Source directory with .bin files
        dest_base: Base destination (e.g., OneDrive path or Google Drive mount)
        obj_id: Object ID (e.g., '000')
        obj_name: Object name (e.g., 'test_object')
        x_angle, y_angle, z_angle: Rotation angles
        exp_num: Experiment number
        is_los: Line-of-sight (True) or non-line-of-sight (False)
        timestamp: Optional specific timestamp to transfer (None = all)
        params: Radar parameters dictionary
        dry_run: If True, don't actually copy files
    """
    # Find bin files
    bin_files = find_bin_files(source_dir, timestamp)
    
    if not bin_files:
        print(f"No .bin files found in {source_dir}")
        return
    
    print(f"Found {len(bin_files)} .bin file(s) to transfer")
    
    # Get radar parameters
    if params is None:
        params = get_radar_params()
    
    # Create destination path following MITO structure
    los_folder = "los" if is_los else "nlos"
    dest_dir = os.path.join(
        dest_base,
        f"{obj_id}_{obj_name}",
        "robot_collected",
        f"{x_angle}_{y_angle}_{z_angle}",
        f"exp{exp_num}",
        los_folder,
        "unprocessed",
        "radars",
        "radar_data"
    )
    
    print(f"\nDestination: {dest_dir}")
    
    if not dry_run:
        os.makedirs(dest_dir, exist_ok=True)
    
    # Transfer each file
    for ts, bin_path in bin_files:
        print(f"\nTransferring timestamp {ts}:")
        
        # New filename without _Raw_0 suffix to match MITO format
        new_bin_name = f"adc_data{ts}.bin"
        dest_bin_path = os.path.join(dest_dir, new_bin_name)
        
        if dry_run:
            print(f"  [DRY RUN] Would copy: {os.path.basename(bin_path)} -> {new_bin_name}")
        else:
            # Copy .bin file
            shutil.copy2(bin_path, dest_bin_path)
            print(f"  Copied: {new_bin_name} ({os.path.getsize(bin_path) / 1024 / 1024:.2f} MB)")
            
            # Create metadata file
            create_metadata_file(bin_path, dest_dir, ts, params)
    
    print(f"\n✓ Transfer complete! {len(bin_files)} file(s) transferred.")
    print(f"  Data location: {dest_dir}")

def main():
    parser = argparse.ArgumentParser(
        description="Transfer radar data from Windows collection to MITO folder structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transfer all files from default Windows location to Google Drive
  python transfer_data_to_drive.py --obj_id 000 --obj_name test_object
  
  # Transfer from custom source to OneDrive
  python transfer_data_to_drive.py --source "D:\\radar_data" --dest "path/to/OneDrive" --obj_id 001 --obj_name apple
  
  # Transfer specific timestamp only
  python transfer_data_to_drive.py --obj_id 000 --obj_name test --timestamp 123456789012
  
  # Dry run (don't actually copy)
  python transfer_data_to_drive.py --obj_id 000 --obj_name test --dry_run
        """
    )
    
    # Source/destination
    parser.add_argument('--source', type=str, 
                       default=r"C:\ti\mmwave_studio_02_01_01_00\mmWaveStudio\PostProc\Data",
                       help='Source directory with .bin files')
    parser.add_argument('--dest', type=str,
                       help='Destination base directory (default: auto-detect Google Drive or OneDrive)')
    
    # Object info
    parser.add_argument('--obj_id', type=str, required=True,
                       help='Object ID (e.g., 000, 001)')
    parser.add_argument('--obj_name', type=str, required=True,
                       help='Object name (e.g., test_object)')
    
    # Experiment parameters
    parser.add_argument('--x_angle', type=int, default=0,
                       help='X rotation angle (default: 0)')
    parser.add_argument('--y_angle', type=int, default=0,
                       help='Y rotation angle (default: 0)')
    parser.add_argument('--z_angle', type=int, default=0,
                       help='Z rotation angle (default: 0)')
    parser.add_argument('--exp_num', type=int, default=1,
                       help='Experiment number (default: 1)')
    parser.add_argument('--los', action='store_true', default=True,
                       help='Line-of-sight experiment (default: True)')
    parser.add_argument('--nlos', dest='los', action='store_false',
                       help='Non-line-of-sight experiment')
    
    # Optional filters
    parser.add_argument('--timestamp', type=int,
                       help='Transfer only specific timestamp')
    parser.add_argument('--config', type=str,
                       help='Path to params.json config file')
    
    # Options
    parser.add_argument('--dry_run', action='store_true',
                       help='Show what would be transferred without actually copying')
    
    args = parser.parse_args()
    
    # Auto-detect destination if not provided
    if args.dest is None:
        # Try common Google Drive and OneDrive locations
        possible_dests = [
            # macOS
            os.path.expanduser("~/Library/CloudStorage/OneDrive-Personal/Documents/fall2025/MAS.361/data"),
            os.path.expanduser("~/Google Drive/Fall_2025/MAS.361/data"),
            # Windows
            os.path.expanduser("~/OneDrive/Documents/fall2025/MAS.361/data"),
            os.path.expanduser("~/Google Drive/Fall_2025/MAS.361/data"),
            # Linux
            os.path.expanduser("~/gdrive/Fall_2025/MAS.361/data"),
        ]
        
        for dest in possible_dests:
            if os.path.exists(dest):
                args.dest = dest
                print(f"Auto-detected destination: {dest}")
                break
        
        if args.dest is None:
            print("Error: Could not auto-detect destination. Please specify --dest")
            return
    
    # Verify source exists
    if not os.path.exists(args.source):
        print(f"Error: Source directory does not exist: {args.source}")
        return
    
    # Load radar parameters
    params = get_radar_params(args.config)
    
    # Transfer data
    transfer_data(
        source_dir=args.source,
        dest_base=args.dest,
        obj_id=args.obj_id,
        obj_name=args.obj_name,
        x_angle=args.x_angle,
        y_angle=args.y_angle,
        z_angle=args.z_angle,
        exp_num=args.exp_num,
        is_los=args.los,
        timestamp=args.timestamp,
        params=params,
        dry_run=args.dry_run
    )

if __name__ == '__main__':
    main()
