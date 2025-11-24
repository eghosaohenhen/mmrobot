## mmRobot

Determining soil moisture content (VWC) using mmWave Radar

## Structure

- src
    - iwr1443 – Submodule for interfacing with the radar
    - utilities - definitions and header files for processing
- processing: data processing pipeline (run in colab)
- 

## Data Structure 

- root 
    - stamped_raw 
        - exp_NUMBER_YYYY-MM-DD_HH-MM-SS.bin (object pose assumed to be [0,0,0])
        OR 
        - exp_NUMBER_x-y-z_YYYY-MM-DD_HH_MM_SS.bin ~x, y, z is the pose ~ 

# TODOs

callback in needs to recursively look in stamped_raw for like the last exp_NUMBER to continue counting up from 
==> make some util function?

# 
