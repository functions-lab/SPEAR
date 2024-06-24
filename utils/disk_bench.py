import os
import time


def write_test_file(file_path, file_size):
    """ Write random data to a file to test write speed. """
    data = os.urandom(file_size)  # Generate random data
    start_time = time.time()
    with open(file_path, 'wb') as file:
        file.write(data)
    end_time = time.time()
    return end_time - start_time  # Return the duration in seconds


def read_test_file(file_path):
    """ Read data from a file to test read speed. """
    start_time = time.time()
    with open(file_path, 'rb') as file:
        data = file.read()
    end_time = time.time()
    return end_time - start_time  # Return the duration in seconds


def main():
    file_path = 'testfile.tmp'
    file_size = 1024 * 1024 * 100  # 100 MB

    # Testing write speed
    write_duration = write_test_file(file_path, file_size)
    write_speed = file_size / write_duration / (1024 * 1024)  # Convert to MB/s

    # Testing read speed
    read_duration = read_test_file(file_path)
    read_speed = file_size / read_duration / (1024 * 1024)  # Convert to MB/s

    print(f"Write Speed: {write_speed:.2f} MB/s")
    print(f"Read Speed: {read_speed:.2f} MB/s")

    # Clean up the test file
    os.remove(file_path)


if __name__ == '__main__':
    main()
