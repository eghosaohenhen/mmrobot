from datetime import datetime

import numpy as np
import socket
from .dcapub import DCAPub
from .dsp import reshape_frame
import argparse
import os
import json

class Radar:

    def __init__(self, cfg_path: str, reshape=True, stamped_data_path= "", host_ip: str = "192.168.33.30",
                 obj_id="000", obj_name="test_object", angles=(0, 0, 0), exp_num=1, is_los=True):
        """
        Initializes the radar object, starts recording, and publishes the data.

        Args:
            cfg_path (str): Path to the .lua file used in mmWaveStudio to configure the radar
            reshape (bool): Whether to reshape the data or not. Default is True.
            stamped_data_path (str): Base path for data storage (e.g., "data/")
            obj_id (str): Object ID (e.g., "001")
            obj_name (str): Object name (e.g., "phillips_screw_driver")
            angles (tuple): (x, y, z) rotation angles in degrees
            exp_num (int): Experiment number
            is_los (bool): True for line-of-sight, False for non-line-of-sight
        """
        print(f"[INFO] Starting radar node with config: {cfg_path}")

        # Configure DCAPub with a conservative socket timeout so recv won't block forever.
        self.radar = DCAPub(
            cfg=cfg_path,
            host_ip=host_ip,
            socket_timeout=2.0,
        )

        self.config = self.radar.config
        self.params = self.radar.params
        self.stamped_data_path = stamped_data_path
        self.obj_id = obj_id
        self.obj_name = obj_name
        self.angles = angles
        self.exp_num = exp_num
        self.is_los = is_los
        self.count = 0
        self.capture_start_time = None
        self.datetime_start_time = None

        
        print("[INFO] Radar connected. Params:")
        print(self.radar.config)

        self.reshape = reshape
    
    # In radar.py - when you start capturing
    def run_polling(self, cb=None, max_no_frame_seconds: float = 10.0):
        """Capture a fixed number of frames, aborting if no new frames arrive for
        `max_no_frame_seconds` to avoid hanging when the stream stalls.
        """
        print("[INFO] Begin capturing data!")
        self.radar.dca1000.flush_data_socket()

        import time

        frames = []
        try:
            
            while len(frames) < self.params['n_frames']:
                try:
                    frame_data, new_frame = self.radar.update_frame_buffer()
                    
                    if new_frame:
                        last_frame_time = time.time()
                        frames.append(frame_data)
                        
                        print(f"[INFO] Captured frame {len(frames)}/{self.params['n_frames']}")
                        continue
                    

                    # If no new frame was returned, check the watchdog
                    if time.time() - last_frame_time >= max_no_frame_seconds:
                        print(f"[WARN] No new frames received for {max_no_frame_seconds} seconds")
                        print(f"[INFO] Captured {len(frames)}/{self.params['n_frames']} frames before timeout")
                        break

                except socket.timeout:
                    print(f"[ERROR] Socket timeout! Captured {len(frames)}/{self.params['n_frames']} frames")
                    # keep waiting until watchdog expires (or break immediately)
                    if time.time() - last_frame_time >= max_no_frame_seconds:
                        break
                    else:
                        continue
                except KeyboardInterrupt:
                    print("[INFO] KeyboardInterrupt received, aborting capture") 
                except Exception as e:
                    print(f"[ERROR] Error receiving frame: {e}")
                    break
            
            # Save all frames with the ONE start timestamp
            if len(frames) > 0:
                self.save_frames(frames, self.datetime_start_time, self.capture_start_time)
                print(f"[INFO] Successfully saved {len(frames)} frames!")
            else:
                print("[ERROR] No frames captured!")
                
        except Exception as e:
            print(f"[ERROR] Exception during frame capture: {e}")
        finally:
            # Ensure the DCA connection is closed on exit
            try:
                self.close()
            except Exception:
                print("[WARN] Exception during radar close")
                pass
    
    def save_frames(self, frames, datetime_start_time, capture_start_time):
        """
        Saves all frames in MITO-compatible folder structure.
        
        Args:
            frames (list): List of frame data arrays
            capture_start_time (float): Timestamp from time.time() when capture started
        """
        # Create MITO folder structure
        x, y, z = self.angles
        los_folder = "los" if self.is_los else "nlos"
        
        # Path: data/{obj_id}_{obj_name}/robot_collected/{x}_{y}_{z}/exp{N}/{los/nlos}/unprocessed/radars/radar_data/
        base_path = os.path.join(
            self.stamped_data_path,
            f"{self.obj_id}_{self.obj_name}",
            "robot_collected",
            f"{x}_{y}_{z}",
            f"exp{self.exp_num}",
            los_folder,
            "unprocessed",
            "radars",
            "radar_data"
        )
        os.makedirs(base_path, exist_ok=True)
        
        # Concatenate all frames into single array
        all_frames = np.concatenate(frames, axis=0)
        
        # Convert to int16 and save as .bin file
        raw_data = np.asarray(all_frames, dtype="<i2")
        
        # Create timestamp string using Unix timestamp
        # Use integer part of timestamp for filename
        timestamp_compact = str(int(capture_start_time))
        
        bin_filename = os.path.join(base_path, f"adc_data{timestamp_compact}.bin")
        with open(bin_filename, "wb") as f:
            raw_data.tofile(f)
        
        print(f"[INFO] Saved {len(frames)} frames to {bin_filename}")
        
        # Save metadata.json in the parent directory (unprocessed/radars/)
        metadata_path = os.path.join(base_path, f"metadata_{timestamp_compact}.json")
        metadata = {
            "capture_start_time": capture_start_time,
            "timestamp_compact": timestamp_compact,
            "datetime_strftime": datetime_start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "num_frames": len(frames),
            "num_samples": self.params['n_samples'],
            "num_chirps": self.params['n_chirps'],
            "num_rx": self.params['n_rx'],
            "num_tx": self.params['n_tx'],
            "periodicity": self.config.get('frameCfg', {}).get('framePeriodicity', 0),
            "sweep_time": self.params.get('sweep_time', 0),
        }
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)
        
        print(f"[INFO] Saved metadata to {metadata_path}")


    def read(self):
        """
        Reads single frame of data from the radar.
        """

        # Flush the data socket to clear any old data
        self.radar.dca1000.flush_data_socket()

        second = False

        try:
            while True:
                frame_data, new_frame = self.radar.update_frame_buffer()

                if new_frame:
                    if not second:
                        second = True
                    else:
                        # structuring the frame data into something digestible for the fft processor 
                        if self.reshape:
                            frame_data = reshape_frame(
                                frame_data,
                                self.params["n_chirps"],
                                self.params["n_samples"],
                                self.params["n_rx"],
                                self.params["n_tx"],
                            )

                        return frame_data
        except KeyboardInterrupt:
            print("[INFO] Stopping frame capture...")

    def flush(self):
        """
        Flushes the data socket to clear any old data.
        """
        self.radar.dca1000.flush_data_socket()

    def close(self):
        """
        Closes the radar connection and stops capturing data.
        """
        self.radar.dca1000.close()
        
        print("[INFO] Radar connection closed.")
