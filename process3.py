# Shared memory to receive return values from spawned new processes


import multiprocessing
import os



class Computation:

    def __init__(self):
        self.c = 10


    def produce_result(self, system_state, result):
        print("Inside Computation.produce_result().  PID: ", os.getpid())
        result.value = self.c + sum(system_state) + os.getpid()



if __name__ == '__main__':
    print("PID of main process: ", os.getpid())

    obj = Computation()

    n_processes = 3
    system_state = [1,2,3,4]

    # create a list of Arrays of int data type with space for 4 integers (one array per process)
    result_list = [multiprocessing.Value('i') for _ in range(n_processes)]


    # Create new processes
    process_list = []
    for i in range(n_processes):
        p = multiprocessing.Process(target=obj.produce_result, args=(system_state, result_list[i]))
        p.start()
        process_list.append(p)


    # Terminate all the process, and get the results
    for i, p in enumerate(process_list):
        p.join()
        print("Result: ", result_list[i].value)
