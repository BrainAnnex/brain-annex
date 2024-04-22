# Using Pool to receive return values from spawned new processes


import multiprocessing
import os
import time



class Computation:

    def __init__(self):
        self.c = 10


    def produce_result(self, system_state, rxn_index):
        s = 0
        for i in range(50_000_000):
            s += i*i

        print("Inside Computation.produce_result().  PID: ", os.getpid())
        print("  system_state: ", system_state)
        print("  rxn_index: ", rxn_index)
        value = self.c + sum(system_state) + rxn_index
        return value



if __name__ == '__main__':
    print("PID of main process: ", os.getpid())

    obj = Computation()

    t_start = time.perf_counter()


    n_processes = 3

    n_reactions = 5

    system_state = [1,2,3,4]
    total_data = [(system_state, rxn_index) for rxn_index in range(n_reactions)]   # List of lists

    # Create a pool object
    p = multiprocessing.Pool(processes=n_processes)
    print(f"Created pool of {n_processes} processes")

    # map list to target function
    result = p.starmap(obj.produce_result, total_data)

    print(result)
    print(f"Finished in {(time.perf_counter() - t_start):.2f} sec")

    print("--- New Iteration ---")

    system_state = result
    total_data = [(system_state, rxn_index) for rxn_index in range(n_reactions)]   # List of lists
    # map list to target function
    result = p.starmap(obj.produce_result, total_data)

    print(result)
    print(f"Finished in {(time.perf_counter() - t_start):.2f} sec")

    p.terminate()
