import os
import numpy as np
from PIL import Image
import cv2
import skimage


def parse_data(
    file_name: str, input_img_size: int, case_numbers: int, time_steps: int, del_t: int
) -> np.ndarray:
    """parse the raw data and return numpy arrays with microstructure images and temp/pressure outputs

    Args:
        file_name (str) : file name of raw data
        input_img_size (int) : pixel size of square input image
        case_numbers (int) : number of cases in the data set
        time_steps (int) : number of time steps used
        del_t (int) : change of time per each time step

    Returns:
        microstructure_data (np.ndarray) : microstructure data
        output_data (np.ndarray) : temp/pressure/temperature_dot/pressure_dot outputs
    """

    # initialize and format data arrays
    microstructure_data = np.zeros((case_numbers, input_img_size, input_img_size, 2))
    output_data = np.zeros(
        (case_numbers, input_img_size, input_img_size, time_steps, 4)
    )  # output dimension 5 shape: [0:T,1:P,2:T_dot,3:P_dot]

    # Generate Distance map (normalized distance from y-axis)
    # Size of the map is same as the original microsturcture image size (485x485)
    wave_map = np.zeros((input_img_size, input_img_size))
    for w in range(1, input_img_size):
        wave_map[:, w] = w / 485.0

    # There are currenly 36 samples that can be used
    for case_idx in range(1, case_numbers + 1):

        # Load Original Microstructure Image
        original_img = (
            "./"
            + file_name
            + "/microstructures/data_"
            + str(format(case_idx, "02d"))
            + ".pgm"
        )
        x = cv2.imread(original_img)
        ori_img = x[:, :, 1]

        # Combine Microstructure image and distance map
        microstructure_data[:, :, :, 0] = ori_img
        microstructure_data[:, :, :, 1] = wave_map

        # load temp and pressure values, clip, and add to output array
        for time_idx in range(0, time_steps):
            # initial time step temp and pressure values
            if time_idx == 0:
                temp = np.full((input_img_size, input_img_size), 300.0)
                output_data[case_idx - 1, :, :, time_idx, 0] = temp
                press = np.full((input_img_size, input_img_size), 0)
                output_data[case_idx - 1, :, :, time_idx, 1] = press
            else:
                temperature_name = (
                    "./data/raw/temperatures/data_"
                    + str(format(case_idx, "02d"))
                    + "/Temp_"
                    + str(format(time_idx, "02d"))
                    + ".txt"
                )
                temperature_img = np.loadtxt(temperature_name)
                # reshape temp values to image size
                temp = np.reshape(temperature_img, (input_img_size, input_img_size))
                # clip the temperature value such that it ranges between 300K and 4000K
                temp = np.clip(temp, 300, 4000)
                output_data[case_idx - 1, :, :, time_idx, 0] = temp

                pressure_name = (
                    "./data/raw/pressures/data_"
                    + str(format(case_idx, "02d"))
                    + "/pres_"
                    + str(format(time_idx, "02d"))
                    + ".txt"
                )
                pressure_img = np.loadtxt(pressure_name)
                # reshape pressure values to image size
                press = np.reshape(pressure_img, (input_img_size, input_img_size))
                output_data[case_idx - 1, :, :, time_idx, 1] = press
                # Calculate T_dot --> T_dot = (T(t+del_t)-T(t))/del_t
                Tdot = (
                    output_data[case_idx - 1, :, :, time_idx, 0]
                    - output_data[case_idx - 1, :, :, time_idx - 1, 0]
                )
                Pdot = (
                    output_data[case_idx - 1, :, :, time_idx, 1]
                    - output_data[case_idx - 1, :, :, time_idx - 1, 1]
                )
                Tdot = Tdot / del_t
                Pdot = Pdot / del_t
                # Save Tdot and Pdot into output data array
                output_data[case_idx - 1, :, :, time_idx, 2] = Tdot
                output_data[case_idx - 1, :, :, time_idx, 3] = Pdot

    # Normalize temp,press,tdot,pdot values to range [-1,1]
    for channel in range(0, 4):
        # Normalize Temperature to range [-1,1]
        norm_max = np.amax(output_data[:, :, :, :, channel])
        norm_min = np.amin(output_data[:, :, :, :, channel])
        output_data[:, :, :, :, channel] = (
            output_data[:, :, :, :, channel] - norm_min
        ) / (norm_max - norm_min)
        output_data[:, :, :, :, channel] = (
            output_data[:, :, :, :, channel] * 2.0
        ) - 1.0
        print("max and min of channel " + str(channel) + " are: ", norm_max, norm_min)

    # Normalize input data to range [-1,1]
    microstructure_data[:, :, :, 0] = (
        microstructure_data[:, :, :, 0] - np.amin(microstructure_data[:, :, :, 0])
    ) / (
        np.amax(microstructure_data[:, :, :, 0])
        - np.amin(microstructure_data[:, :, :, 0])
    )
    microstructure_data[:, :, :, 1] = (
        microstructure_data[:, :, :, 1] - np.amin(microstructure_data[:, :, :, 1])
    ) / (
        np.amax(microstructure_data[:, :, :, 1])
        - np.amin(microstructure_data[:, :, :, 1])
    )
    microstructure_data[:, :, :, 0] = microstructure_data[:, :, :, 0] > 0.5
    microstructure_data = (microstructure_data * 2.0) - 1.0

    output_data = output_data[:, :480, :480, :, :]
    microstructure_data = microstructure_data[:, :480, :480, :]
    # downsample to half of image size
    output_data = skimage.measure.block_reduce(output_data, (1, 2, 2, 1, 1), np.max)
    microstructure_data = skimage.measure.block_reduce(
        microstructure_data, (1, 2, 2, 1), np.mean
    )
    microstructure_data[:, :, :, :1] = microstructure_data[:, :, :, :1] > 0
    microstructure_data[:, :, :, :1] = (microstructure_data[:, :, :, :1] * 2.0) - 1.0

    print("Finished Processing Data")
    print("shape of microstructure data is: ", microstructure_data.shape)
    print("shape of output data is: ", output_data.shape)

    return microstructure_data, output_data


def split_data(
    data_in: np.ndarray, output_data: np.ndarray, splits: list
) -> np.ndarray:
    """split the data into training, validation, and testing cases

    Args:
        data_in (np.ndarray): microstructure data
        output_data (np.ndarray): temp/pressure/temperature_dot/pressure_dot outputs
        splits (list[int]): train, val, test split

    Returns:
        X_train, y_train, X_val, y_val, test_X, test_Y (np.ndarray): split data
    """
    case_numbers = len(output_data)
    print(case_numbers)
    train = case_numbers * splits[0]
    valid = train + (case_numbers * splits[1])
    test = valid + (case_numbers * splits[2])
    train = int(train)
    valid = int(valid)
    test = int(test)
    print(train)
    print(valid)
    print(test)

    # Training
    X_train = data_in[:train, :, :, :]
    y_train = output_data[:train, :, :, :, :]

    # Validation
    X_val = data_in[train:valid, :, :, :]
    y_val = output_data[train:valid, :, :, :, :]

    # Test
    test_X = data_in[valid:test, :, :, :]
    test_Y = output_data[valid:test, :, :, :, :]

    print(X_train.shape)
    print(y_train.shape)
    print(X_val.shape)
    print(y_val.shape)
    print(test_X.shape)
    print(test_Y.shape)
    return X_train, y_train, X_val, y_val, test_X, test_Y

def reshape(old_data: np.ndarray):
    """reshapes data from new format to old (5 dimensional to 4 dimensional)
    Args:
        old_data (np.ndarray): output data in 5 dimensional format
    Returns:
        new_data (np.ndarray): output data in 4 dimensional format
    """
    case_numbers = len(old_data)
    case_numbers = int(case_numbers)
    time_steps = old_data.shape[3]
    img_size = old_data.shape[2]
    new_data = np.zeros( (case_numbers,img_size,img_size,((time_steps*4)-2)) )
    print("Old shape of data: ",old_data.shape)
    
    for case_idx in range (case_numbers):
        for time_idx in range(time_steps):
            new_data[case_idx,:,:,(2*time_idx)] = old_data[case_idx,:,:,time_idx,0]
            new_data[case_idx,:,:,(2*time_idx)+1] = old_data[case_idx,:,:,time_idx,1]
        for time_idx in range(time_steps-1):
            new_data[case_idx,:,:,(2*time_steps)+(2*time_idx)] = old_data[case_idx,:,:,time_idx+1,2]
            new_data[case_idx,:,:,(2*time_steps)+(2*time_idx)+1] = old_data[case_idx,:,:,time_idx+1,3]
    
    print("New shape of data: ",new_data.shape)
                
    return new_data
