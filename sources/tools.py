from abc import abstractmethod
from multiprocessing import Queue, Process
from uuid import uuid1


class ProcessService:
    """ Represent the service executed in own thread

    The single unit that work in own process
    The instances on that class will be wired in Manager
    and then turned into single multiprocess chain where
    each node will communicate via input and output buffer

    Attributes:
        output_buffer (Queue): Is used to send data for next node of the chain
        input_buffer (Queue): Is used to receive data from previous node of the chain

    """

    def __init__(self):
        """Initialize empty buffers that later will be fill in manager during node wiring """
        self.output_buffer = None
        self.input_buffer = None

    def set_input_buffer(self, buffer: Queue):
        """Set the input buffer

        Args:
            buffer (Queue): Is used to receive data from previous node of the chain

        Returns:
            None

        """
        self.input_buffer = buffer

    def set_output_buffer(self, buffer: Queue):
        """ Set the output buffer

        Args:
            buffer (Queue): Is used to receive data from previous node of the chain

        Returns:
            None

        """
        self.output_buffer = buffer

    @abstractmethod
    def act(self):
        """ Method passed as the target to the process

        In implementation of that method must be the main behaviour of the instance
        Here shod be code responsible for both reading data from input_buffer and
        produces data to output_buffer. Also here should be functional responsible for
        data transformation between input_buffer and output_buffer

        Returns:
            None

        """
        pass


class Manager:
    """ Represent manager that wires and manage ProcessService instances

    The main purpose of that class is to bring functional to
    easily connect nodes or ProcessService instances together
    by smart and continuous injecting buffers(Queue instances)
    into them

    Attributes:
        services ([ProcessService]): the chain of wired ProcessServices
        processes (Process): the running processes which is executing node act() method

    """

    def __init__(self, services: [ProcessService]):
        """ Initialize services chain array and empty processes array for future usage

        Args:
            services ([ProcessService]) the array of not wired ProcessServices

        """
        self.services = []
        self.processes = []
        for key, service in enumerate(services):
            output_buffer = Queue()
            if key == 0:
                input_buffer = Queue()
            else:
                input_buffer = self.services[-1].output_buffer
            service.set_input_buffer(input_buffer)
            service.set_output_buffer(output_buffer)
            self.services.append(service)

    def start(self):
        """ Start new process for each ProcessService instance in services array
         Pass ProcessInstance act() method as target for related process
         Append each running process to processes

         Returns:
             None
        """
        for service in self.services:
            process = Process(target=service.act, args=())
            process.start()
            self.processes.append(process)

    def __enter__(self):
        for service in self.services:
            process = Process(target=service.act, args=())
            process.start()
            self.processes.append(process)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def send(self, data):
        """ Pass data for first chain node input buffer

        Args:
            data: Any data

        Returns:
            None

        """
        self.services[0].input_buffer.put(data)

    def receive(self, block: bool = True, timeout: int = None):
        """ Receive data from the last chain node output data

        Args:
            block (bool): If true than block program
                         executing while data will appeared in buffer
            timeout (int): Set the block timeout

        Return:
            None, any data

        """
        buffer = self.services[-1].output_buffer
        if block or not buffer.empty():
            return buffer.get(block, timeout)
        else:
            return None


class Client(Manager):
    """Implementation of Manager"""

    def __init__(self, services: [ProcessService]):
        """ Set unique id for connected client

        Args:
            services ([ProcessService]) the array of not wired ProcessServices

        """
        super().__init__(services)
        self.id = uuid1()
        self.running = False

