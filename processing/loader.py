"""
This file is responsible for loading and saving data from the dataset
It manages the proper folder structure for data in the dataset
"""

import os
import pickle
import numpy as np
from PIL import Image
from utils import *
import json

from utils import *



class GenericLoader:

    def __init__(self, obj_id: str, name: str, is_sim=True, is_los=True, exp_num=1):
        """
        Initializes GenericLoader for loading data from the dataset

        Parameters:
            obj_id (str): id of the object (e.g. "001"). Note: This ID is expected to be the full 3 digit long ID, including leading zeros.
            name (str): name of the object (e.g. "phillips_screw_driver"). Note: This name is expected to match the official name in the YCB dataset (including underscores, not spaces)
            is_sim (bool): True if loading or saving data from simulation environment
            is_los (bool): True if line-of-sight experiment. False for non-line-of-sight. This parameter is ignored for simulation data
            exp_num (int): Experiment number. None or 'None' will default to 1. This is ignored if using simulation
        """
        self.obj_id = obj_id
        self.name = name
        self.is_sim = is_sim
        self.is_los = is_los
        if exp_num == 'None' or exp_num is None: exp_num = 1
        self.exp_num = exp_num
    def get_radar_parameters(radar_type='77_ghz', is_sim=False, aperture_type='test'):
        """
        Load the radar parameters from the json file.

        Parameters:
            radar_type (str): '77_ghz'
            is_sim (str): Is simulation data
            aperture_type (str): 'normal' or 'test'
        Returns:
            radar parameters (dictionary)
        """
        
        f = open(f'{get_root_path()}/src/utilities/params.json')
        params = json.load(f)
        current = params['simulation' if is_sim else 'robot_collected'][radar_type]
        if not is_sim:
            current = current[aperture_type]
        return current
    def _find_obj_angles(self):
        """
        Finds the object angles for the given experiment number. 
        This function will iterate through each angle folder to find the matching exp folder. 
        This assumes the matching exp data has been downloaded from AWS.

        Returns:
            a list of integers cooresponding to the X, Y, Z angles of the object for this experiment
        """
        # dummy code for now - in reality this would search the folders
        if self.is_sim: return (0, 0, 0) # Default to 0,0,0 for simulation data
        return (0, 0, 0) # Placeholder for real implementation
    def _get_path(self, radar_type, x_angle, y_angle, z_angle, is_processed=False):
        """
        Get the root path for the given radar type and object angles

        Parameters:
            radar_type (str): the type of radar to use ("24_ghz", "77_ghz")
            x_angle (int): rotation angle in degrees of the loading object
            y_angle (int): rotation angle in degrees of the loading object
            z_angle (int): rotation angle in degrees of the loading object
            is_processed (bool): whether to get the path for processed data or raw data
        """
        # Implement the logic to construct the path based on the parameters
        base_path = get_root_path()
        if self.is_sim:
            base_path = get_sim_path()
        else:
            base_path = get_data_path()

        # processed_folder = "processed" if is_processed else "raw"
        # path = os.path.join(base_path, radar_type, f"x_{x_angle}", f"y_{y_angle}", f"z_{z_angle}", processed_folder)
        path = base_path
        return path

    def load_radar_files(self, radar_type, aperture_type='test'):
        """
        Load raw radar files for processing (Note: this function is only needed when processing raw radar data into an image)
        
        Parameters:
            radar_type (str): the type of radar to use ("24_ghz", "77_ghz")
            angle (int): rotation angle in degrees of the loading object

        Returns: 
            Loaded complex-valued radar (adc) files for the specified radar type
        """
        x_angle, y_angle, z_angle = self._find_obj_angles()
        path = self._get_path(radar_type, x_angle, y_angle, z_angle, is_processed=False) + "/radar_data"
        all_data = {}
        filenames = sorted(os.listdir(path))
        params_dict = self.get_radar_parameters(radar_type=radar_type, is_sim=False, aperture_type=aperture_type)
        NUM_FRAMES = params_dict['num_frames']
        SAMPLES_PER_CHIRP = params_dict['num_samples']
        NUM_CHIRP = params_dict['num_chirps']
        for i, filename in enumerate(filenames):
            if filename[-4:] != '.bin': continue
            
            # Parse filename: exp_NUMBER_YYYY-MM-DD_HH-MM-SS.bin or exp_NUMBER_x-y-z_YYYY-MM-DD_HH_MM_SS.bin
            try:
                # Remove .bin extension
                name_without_ext = filename[:-4]
                parts = name_without_ext.split('_')
                
                # Find the timestamp part (starts with year YYYY)
                timestamp_str = None
                for idx, part in enumerate(parts):
                    if len(part) >= 4 and part[:4].isdigit() and int(part[:4]) >= 2000:
                        # Found the start of timestamp, combine remaining parts
                        timestamp_parts = parts[idx:]
                        timestamp_str = '_'.join(timestamp_parts)
                        break
                
                if timestamp_str is None:
                    print(f'Could not parse timestamp from filename: {filename}')
                    continue
                
                # Use the timestamp string as the key (can convert to datetime if needed later)
                timestamp = timestamp_str.replace('-', '').replace('_', '')  # Convert to compact format
                
            except Exception as e:
                print(f'Error parsing filename {filename}: {e}')
                continue

            fid = open(f'{path}/{filename}', 'rb')
            adcData = np.fromfile(fid, dtype='<i2')
            numLanes = 4
            adcData = np.reshape(adcData, (int(adcData.shape[0] / (numLanes * 2)), numLanes * 2))
            adcData = adcData[:, [0, 1, 2, 3]] + 1j * adcData[:, [4, 5, 6, 7]]
            all_data[timestamp] = adcData

        return all_data