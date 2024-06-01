import time
import socket
import pickle
import numpy as np
import matplotlib.pyplot as plt
import threading


def setup_plot(title):
    """ Set up the initial plot window with a specific title """
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_title(title)
    ax.set_xlabel('Sample Index')
    ax.set_ylabel('Amplitude')
    line, = ax.plot([], [], label='Real Part')
    line_imag, = ax.plot([], [], label='Imaginary Part')
    ax.set_ylim(np.iinfo(np.int16).min / 4, np.iinfo(np.int16).max / 4)
    ax.legend()
    ax.grid(True)
    return fig, ax, line, line_imag


def update_plot(ax, line_real, line_imag, data, plot_ratio=0.01):
    """ Update the plot with a subset of new data based on the plot ratio """
    num_points = int(len(data) * plot_ratio)
    # Update the plot with only the portion of data specified by plot_ratio
    if num_points > 0:  # Ensure there's at least one point to plot
        time_indices = np.arange(num_points)
        line_real.set_data(time_indices, data.real[:num_points])
        line_imag.set_data(time_indices, data.imag[:num_points])
        ax.set_xlim(0, num_points - 1)  # Adjust x-axis to the new data length
    else:
        # Clear data if no points are to be plotted
        line_real.set_data([], [])
        line_imag.set_data([], [])

    ax.relim()  # Recompute the ax.dataLim
    ax.autoscale_view()  # Update the axis view
    plt.draw()
    plt.pause(0.0001)


def receive_array(sock, max_buffer_size=1000000):
    """Receive the data in small chunks and reconstruct the array, with a timeout."""
    full_data = b''
    start_time = time.time()  # Record the start time

    while len(full_data) < max_buffer_size:
        data = sock.recv(max_buffer_size)
        if not data:
            break
        full_data += data
        if time.time() - start_time > 30:  # Check if time exceeded 30 second
            break
    try:
        restore_numpy = pickle.loads(full_data)
    except Exception as e:
        print(f"Failed to deserialize numpy. Buffer discarded. Error: {e}")
        # Return a minimal complex array in case of error
        return np.zeros(1)

    return restore_numpy


def server_program(host, port, title):
    fig, ax, line_real, line_imag = setup_plot(title)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen()
        print(f"Listening on {host}:{port} for {title}")
        while True:
            connection, addr = sock.accept()
            print(f"Connection from: {addr} for {title}")
            try:
                while True:
                    array = receive_array(connection)
                    update_plot(ax, line_real, line_imag, array)
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                connection.close()


# Example usage
if __name__ == "__main__":
    host = socket.gethostname()
    threading.Thread(target=server_program, args=(
        host, 1234, 'IQ Samples From ADC')).start()
