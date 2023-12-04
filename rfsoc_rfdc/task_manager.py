from .overlay_task import OverlayTask, RfdcTask


class TaskManager:
    def __init__(self, num_jobs):
        self.tasks = []
        self.append(RfdcTask())

    def execute_all(self):
        # Start all tasks
        for task in self.tasks:
            task.start()

        # Wait for all tasks to complete
        for task in self.tasks:
            task.join()

    def list_IPs(self):
        print("This overlay contains the following IPs:")
        for ip in self.ip_dict:
            print(ip)

    def transmitter_start(self, sequence):
        self.radio_transmitter.data(sequence)
        self.radio_transmitter.start()

    def receiver_start(self):
        self.radio_receiver.monitor.start()
        print("Receiver ends")
