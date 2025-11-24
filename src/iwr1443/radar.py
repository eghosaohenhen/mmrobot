from datetime import datetime

import numpy as np
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

        self.radar = DCAPub(
            cfg=cfg_path,
            host_ip=host_ip
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
    def run_polling(self, cb=None):
        print("[INFO] Begin capturing data!")
        self.radar.dca1000.flush_data_socket()
        # self.datetime_start_time = datetime.now()
        
        # ONE timestamp for the whole capture session (includes microseconds)
        import time
        # self.capture_start_time = time.time()  # Unix timestamp with microseconds
        
        
        frames = []
        try:
            while len(frames) < self.params['n_frames']:
                frame_data, new_frame = self.radar.update_frame_buffer()
                if new_frame and len(frames) == 0:
                    # Store the exact datetime of the first frame capture
                    self.datetime_start_time = datetime.now()
                    self.capture_start_time = time.time()
                if new_frame:
                    frames.append(frame_data)
                    print(f"[INFO] Captured frame {len(frames)}/{self.params['n_frames']}")
            
            # Save all frames with the ONE start timestamp
            self.save_frames(frames, self.datetime_start_time, self.capture_start_time)
            print(f"[INFO] Successfully saved {len(frames)} frames!")
        except KeyboardInterrupt:
            self.close()
            print("[INFO] Stopping radar...")
    
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
        
        # Create timestamp string (compact format like MITO: YYYYMMDDHHMMSS)
        from datetime import datetime
        dt = datetime.fromtimestamp(capture_start_time)
        timestamp_compact = dt.strftime("%Y%m%d%H%M%S")
        
        bin_filename = os.path.join(base_path, f"adc_data{timestamp_compact}.bin")
        with open(bin_filename, "wb") as f:
            raw_data.tofile(f)
        
        print(f"[INFO] Saved {len(frames)} frames to {bin_filename}")
        
        # Save metadata.json in the parent directory (unprocessed/radars/)
        metadata_path = os.path.join(base_path, "..", "metadata.json")
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
    # def run_polling(self, cb=None):
    #     print("[INFO] Begin capturing data!")

    #     # Flush the data socket to clear any old data
    #     self.radar.dca1000.flush_data_socket()

    #     try:
    #         while True:
    #             frame_data, new_frame = self.radar.update_frame_buffer()

    #             if new_frame:
                    
                    

    #                 # saving the raw frame data (like mmWave studio does) to a timestamped_bin file
    #                 ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # cuz windows hates colons
    #                 day = datetime.now().strftime("%Y-%m-%d")
    #                 folder = rf"{self.stamped_data_path}{day}"
    #                 raw_data = np.asarray(frame_data, dtype="<i2").ravel()
    #                 os.makedirs(folder, exist_ok=True)
    #                 with open(f"{folder}\\adc_data{self.count}_{ts}.bin","wb") as f:
    #                     raw_data.tofile(f)
    #                     self.count += 1
                    
    #                 # If reshaping is enabled, reshape the frame data
    #                 # if self.reshape:
    #                 #     frame_data = reshape_frame(
    #                 #         frame_data,
    #                 #         self.params["n_chirps"],
    #                 #         self.params["n_samples"],
    #                 #         self.params["n_rx"],
    #                 #         self.params["n_tx"],
    #                 #     )

    #                 msg = {
    #                     "data": raw_data,
    #                     "timestamp": timestamp,
    #                 }

    #                 if cb:
    #                     cb(msg)

        # except KeyboardInterrupt:
        #     self.close()
            
            
        #     print("[INFO] Stopping radar...")

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
