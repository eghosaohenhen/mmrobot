# mmRobot - IWR1443 Radar Data Collection

Radar data collection system for the TI IWR1443 mmWave radar using the DCA1000 capture card. This codebase enables SAR (Synthetic Aperture Radar) imaging compatible with the [MITO dataset](https://github.com/signalkinetics/MITO_Codebase).

## Hardware Requirements

- **Radar**: Texas Instruments IWR1443 Boost EVM
- **Capture Card**: DCA1000 EVM
- **Network**: Ethernet connection between PC and DCA1000
- **Software**: mmWave Studio (TI) with DCA1000 CLI tools

## Repository Structure

```
mmrobot/
├── src/
│   ├── iwr1443/          # Python interface for IWR1443 radar
│   │   ├── radar.py      # Main radar class
│   │   ├── dca1000.py    # DCA1000 Ethernet interface
│   │   ├── dcapub.py     # Data capture publisher
│   │   └── dsp.py        # Signal processing utilities
│   └── utilities/
│       └── params.json   # Radar configuration parameters
├── radar-scripts/
│   ├── 1443_mmwavestudio_config.lua          # mmWave Studio config
│   └── DataCaptureDemo_xWR_cli_continuous.lua # Alternative config with GUI automation
├── processing/
│   └── loader.py         # Data loader for MITO compatibility
├── imaging.py            # Main data collection script (Python-based)
├── click_gui_continuous.py # Alternative Windows GUI automation script
├── transfer_data_to_drive.py # Transfer collected data to MITO folder structure
└── cf.json              # DCA1000 configuration file
```

## Network Configuration

Your setup should use the following IP addresses:

- **Host PC (Windows)**: `192.168.33.42`
- **DCA1000 EVM**: `192.168.33.180`
- **MAC Address**: `12:34:56:78:90:12`

Configure your PC's Ethernet adapter to use the static IP `192.168.33.42` with subnet mask `255.255.255.0`.

## Radar Configuration

Current radar parameters (consistent across all scripts):

| Parameter | Value | Description |
|-----------|-------|-------------|
| Start Frequency | 77.5 GHz | Beginning of frequency sweep |
| End Frequency | 80.5 GHz | End of frequency sweep (3 GHz bandwidth) |
| Frequency Slope | 58.594 MHz/µs | Chirp slope |
| ADC Samples | 512 | Samples per chirp |
| Sample Rate | 10 MHz | ADC sampling rate |
| Ramp End Time | 60 µs | Chirp duration |
| Idle Time | 100 µs | Time between chirps |
| RX Channels | 4 | Active receive antennas |
| TX Channels | 1 | Active transmit antenna (TX0) |
| Chirp Loops | 1 | Chirps per frame |
| Frame Periodicity | 3 ms | Time between frames |
| Number of Frames | 4000 | Total frames per capture |
| RX Gain | 30 dB | Receiver gain |

**Total capture size per session**: ~16.4 MB (4000 frames × 512 samples × 1 chirp × 4 RX × 2 bytes × 2 (I/Q))

**Total capture duration**: ~12 seconds (4000 frames × 3 ms)

## Installation

### Prerequisites
- Python 3.10+
- `uv` package manager (recommended) or `pip`
- Windows OS (for mmWave Studio and DCA1000 tools)

### Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd mmrobot

# Install dependencies with uv
uv pip install -r requirements.txt

# Or with pip in a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Data Collection Methods

You have **two options** for collecting radar data, both save data in MITO-compatible format.

---

## Method 1: Python-Based Collection (Recommended)

**Best for**: Direct control, simpler setup, no GUI automation needed

### How to Run

```bash
# Basic usage
uv run imaging.py --cfg radar-scripts/1443_mmwavestudio_config.lua \
  --obj_id 000 --obj_name test_object

# With experiment parameters
uv run imaging.py --cfg radar-scripts/1443_mmwavestudio_config.lua \
  --obj_id 001 --obj_name apple \
  --x_angle 0 --y_angle 0 --z_angle 0 \
  --exp_num 1 --los

# For non-line-of-sight
uv run imaging.py --cfg radar-scripts/1443_mmwavestudio_config.lua \
  --obj_id 002 --obj_name coffee_mug \
  --exp_num 1 --nlos
```

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--cfg` | str | Required | Path to .lua configuration file |
| `--obj_id` | str | `"000"` | Object ID (3 digits with leading zeros) |
| `--obj_name` | str | `"test_object"` | Object name (use underscores) |
| `--x_angle` | int | `0` | X-axis rotation angle (degrees) |
| `--y_angle` | int | `0` | Y-axis rotation angle (degrees) |
| `--z_angle` | int | `0` | Z-axis rotation angle (degrees) |
| `--exp_num` | int | `1` | Experiment number |
| `--los` / `--nlos` | flag | `--los` | Line-of-sight or non-line-of-sight |

### What to Expect

```
[INFO] Starting radar node with config: radar-scripts/1443_mmwavestudio_config.lua
[INFO] Radar connected. Params:
{'frameCfg': {...}, 'profileCfg': {...}}
[INFO] Begin capturing data!
[INFO] Captured frame 1/4000
[INFO] Captured frame 2/4000
...
[INFO] Captured frame 4000/4000
[INFO] Saved 4000 frames to data/000_test_object/robot_collected/0_0_0/exp1/los/unprocessed/radars/radar_data/adc_data173235678912.bin
[INFO] Saved metadata to data/000_test_object/robot_collected/0_0_0/exp1/los/unprocessed/radars/radar_data/metadata_173235678912.json
[INFO] Successfully saved 4000 frames!
```

### Output Files

Data is saved in MITO-compatible folder structure:

```
data/
└── {obj_id}_{obj_name}/
    └── robot_collected/
        └── {x}_{y}_{z}/
            └── exp{N}/
                └── los/ (or nlos/)
                    └── unprocessed/
                        └── radars/
                            └── radar_data/
                                ├── adc_data{timestamp}.bin
                                └── metadata_{timestamp}.json
```

**Example**:
```
data/000_test_object/robot_collected/0_0_0/exp1/los/unprocessed/radars/radar_data/
├── adc_data173235678912.bin
└── metadata_173235678912.json
```

### Metadata Contents

The `metadata_{timestamp}.json` file contains:
```json
{
    "capture_start_time": 1732356789.12,
    "timestamp_compact": "173235678912",
    "datetime_strftime": "2025-11-24 14:31:59.120000",
    "num_frames": 4000,
    "num_samples": 512,
    "num_chirps": 1,
    "num_rx": 4,
    "num_tx": 1,
    "periodicity": 3,
    "sweep_time": 0.00006
}
```

---

## Method 2: Windows GUI Automation (Advanced)

**Best for**: Automated robot scanning, OptiTrack integration, multi-measurement sessions

### Prerequisites

1. **mmWave Studio** must be running and configured
2. **DCA1000 CLI tools** installed at: `C:\ti\mmwave_studio_02_01_01_00\mmWaveStudio\PostProc\`
3. Radar already configured using `DataCaptureDemo_xWR_cli_continuous.lua`

### How to Run

```bash
# For manual testing (no robot)
# First, edit click_gui_continuous.py: set use_robot_comp = False
python click_gui_continuous.py

# For robot-synchronized collection
# Ensure robot computer is at 192.168.41.146:8080
python click_gui_continuous.py
```

### What to Expect

```
C:\path\to\mmrobot
Connected to DCA1000!
connected to the server!
About to recieve
Recieved b'M'
Taking measurement 0
Sending 173235678912,1732356789.1,1732356801.2
About to recieve
Recieved b'M'
Taking measurement 1
...
```

### Output Files

Data saved to: `C:\ti\mmwave_studio_02_01_01_00\mmWaveStudio\PostProc\Data\`

Files generated:
- `adc_data_{timestamp}_Raw_0.bin` - Raw radar data

**Note**: This method saves raw files that need to be transferred to MITO folder structure (see next section).

---

## Transferring Data to MITO Structure

If you collected data with Method 2 (GUI automation), use the transfer script:

```bash
# Basic transfer
python transfer_data_to_drive.py \
  --source "C:\ti\mmwave_studio_02_01_01_00\mmWaveStudio\PostProc\Data" \
  --obj_id 000 --obj_name test_object

# With custom destination
python transfer_data_to_drive.py \
  --source "C:\path\to\data" \
  --dest "D:\OneDrive\Documents\fall2025\MAS.361\data" \
  --obj_id 001 --obj_name apple \
  --exp_num 1 --los

# Transfer specific timestamp only
python transfer_data_to_drive.py \
  --obj_id 000 --obj_name test \
  --timestamp 173235678912

# Dry run (preview without copying)
python transfer_data_to_drive.py \
  --obj_id 000 --obj_name test --dry_run
```

The transfer script will:
1. Find all `.bin` files in the source directory
2. Create MITO folder structure
3. Rename files to MITO format (`adc_data{timestamp}.bin`)
4. Generate `metadata_{timestamp}.json` files
5. Copy everything to the destination

---

## Processing Data with MITO

After collecting data, process it into SAR images using the MITO notebook:

1. Upload data to Google Drive at: `/Fall_2025/MAS.361/data/`
2. Open `mito_project.ipynb` in Google Colab
3. Run the notebook cells to:
   - Mount Google Drive
   - Load your IWR1443 data
   - Generate SAR images
   - Visualize results

See the [MITO_Codebase README](https://github.com/signalkinetics/MITO_Codebase) for detailed processing instructions.

---

## Troubleshooting

### "No frames captured"
- Check network connection (ping `192.168.33.180`)
- Verify radar is powered on and firmware loaded
- Ensure DCA1000 is in operational mode (green LED)

### "Connection refused"
- Verify PC IP is set to `192.168.33.42`
- Check firewall settings (allow UDP ports 4096, 4098)
- Restart DCA1000 and mmWave Studio

### "File size incorrect"
- Verify radar configuration matches expected parameters
- Check `cf.json` `bytesToCapture` value (should be 16,384,000)
- Ensure sufficient disk space

### "GUI automation not working" (Method 2)
- Check mmWave Studio window position
- Adjust `pyautogui.click()` coordinates in `click_gui_continuous.py`
- Ensure mmWave Studio is focused and visible

---

## Key Differences Between Methods

| Feature | Method 1 (Python) | Method 2 (GUI) |
|---------|------------------|----------------|
| **Ease of Use** | ✅ Simple | ⚠️ Complex |
| **Setup** | Python only | mmWave Studio + DCA1000 CLI |
| **Output Format** | MITO-ready | Requires transfer script |
| **Robot Sync** | ❌ Not built-in | ✅ Socket-based sync |
| **OptiTrack** | ❌ Not supported | ✅ Supported |
| **Metadata** | ✅ Auto-generated | ⚠️ Generated during transfer |
| **Best For** | Single captures, testing | Automated scanning, research |

---

## Citation

This codebase is designed to work with the MITO dataset. If you use this for your research, please cite:

```bibtex
@misc{dodds2025mitoenablingnonlineofsightperception,  
      title={MITO: Enabling Non-Line-of-Sight Perception using Millimeter-waves through Real-World Datasets and Simulation Tools},   
      author={Laura Dodds and Tara Boroushaki and Fadel Adib},  
      year={2025},  
      eprint={2502.10259},  
      archivePrefix={arXiv},  
      primaryClass={cs.CV},  
      url={https://arxiv.org/abs/2502.10259}
}
```

---

## License

[Add your license here]

## Contact

[Add your contact information here]
