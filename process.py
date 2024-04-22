from multiprocessing import Process
import os


v = 123

def foo():
    print("Inside foo().  PID: ", os. getpid())
    print("v = ", v)


if __name__ == '__main__':
    num_cores = os.cpu_count()

    print("# cores: ", num_cores)
    print("PID of main process: ", os. getpid())

    foo()

    p = Process(target=foo)

    v = 999

    foo()

    p.start()
