import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat
import argparse
import os


def plot_complex_components(filename):
    # Determine the file type from the file extension
    file_extension = os.path.splitext(filename)[1].lower()

    # Load the complex array from the file
    if file_extension == '.npy':
        data = np.load(filename)
    elif file_extension == '.mat':
        mat_data = loadmat(filename)
        # Assuming the variable name in .mat file is 'data'
        data = mat_data['wave'].squeeze()
    else:
        raise ValueError("Unsupported file type. Use a .npy or .mat file.")

    # Time array for x-axis
    time = np.arange(len(data))

    # Create a plot
    plt.figure(figsize=(10, 5))
    plt.title('Real and Imaginary Parts of the Complex Data')
    plt.plot(time, data.real, label='Real Part')
    plt.plot(time, data.imag, label='Imaginary Part')
    plt.xlabel('Sample Index')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Plot complex components from npy or mat file.')
    parser.add_argument('filename', type=str,
                        help='Path to the npy or mat file.')

    # Parse arguments
    args = parser.parse_args()

    # Call the function with parsed arguments
    plot_complex_components(args.filename)
