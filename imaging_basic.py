import argparse
from src.iwr1443.radar import Radar
import numpy as np
from PyQt6 import QtWidgets
from src.distance_plot import DistancePlot
import sys
from scipy.fft import fft, fftfreq
import os
from utils import *
from multiprocessing import Process, Pipe
import time

# Base data path - will create MITO folder structure under this
DATA_PATH = os.path.join(get_root_path(), "data")



def background_subtraction(frame):
    after_subtraction = np.zeros_like(frame)
    for i in range(1, frame.shape[0]):
        after_subtraction[i - 1] = frame[i] - frame[i - 1]

    return after_subtraction



def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True, help="Path to radar config file")
    parser.add_argument("--obj_id", type=str, default="000", help="Object ID (e.g., 001)")
    parser.add_argument("--obj_name", type=str, default="test_object", help="Object name (e.g., phillips_screw_driver)")
    parser.add_argument("--x_angle", type=int, default=0, help="X rotation angle in degrees")
    parser.add_argument("--y_angle", type=int, default=0, help="Y rotation angle in degrees")
    parser.add_argument("--z_angle", type=int, default=0, help="Z rotation angle in degrees")
    parser.add_argument("--exp_num", type=int, default=1, help="Experiment number")
    parser.add_argument("--los", action="store_true", help="Line-of-sight experiment (default: True)")
    parser.add_argument("--nlos", action="store_true", help="Non-line-of-sight experiment")
    args = parser.parse_args()

    # Determine line-of-sight setting
    is_los = not args.nlos  # Default to LOS unless --nlos is specified

    # Initialize the radar with MITO folder structure
    print("Initializing radar with MITO folder structure...")
    print(f"  Object: {args.obj_id}_{args.obj_name}")
    print(f"  Angles: ({args.x_angle}, {args.y_angle}, {args.z_angle})")
    print(f"  Experiment: exp{args.exp_num}")
    print(f"  Type: {'los' if is_los else 'nlos'}")
    print(f"  Data path: {DATA_PATH}")

    radar = Radar(
        cfg_path=args.cfg,
        stamped_data_path=DATA_PATH,
        host_ip="192.168.33.30",
        obj_id=args.obj_id,
        obj_name=args.obj_name,
        angles=(args.x_angle, args.y_angle, args.z_angle),
        exp_num=args.exp_num,
        is_los=is_los
    )
    print("Radar initialized successfully!")

    
    radar.run_polling(cb=generic_cb)

    
    # Initalize the GUI
    # app = QtWidgets.QApplication(sys.argv)
    # dist_plot = DistancePlot(params["range_res"])
    # dist_plot.resize(600, 600)
    # dist_plot.show()
    def generic_cb(msg):
        print(f"got frame at time {msg["timestamp"]}")
    # def update_frame(msg):
    #     frame = msg.get("data", None)
    #     if frame is None:
    #         return
        
    #     frame = background_subtraction(frame)

    #     # Get the fft of the data
    #     signal = np.mean(frame, axis=0)

    #     fft_result = fft(signal, axis=0)
    #     fft_freqs = fftfreq(SAMPLES_PER_CHIRP, 1 / SAMPLE_RATE)
    #     fft_meters = fft_freqs * c / (2 * FREQ_SLOPE)

    #     # Plot the data
    #     dist_plot.update(
    #         fft_meters[: SAMPLES_PER_CHIRP // 2],
    #         np.abs(fft_result[: SAMPLES_PER_CHIRP // 2, :]),
    #     )

    #     app.processEvents()

    # Initialize the radar

    


if __name__ == "__main__":
    main()
