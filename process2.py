from multiprocessing import Process
import os




class foo:

    def __init__(self):
        self.v = 123


    def explain(self):
        print("Inside foo.explain().  PID: ", os. getpid())
        print("v = ", self.v)



if __name__ == '__main__':
    num_cores = os.cpu_count()

    print("# cores: ", num_cores)
    print("PID of main process: ", os. getpid())

    obj = foo()
    obj.explain()

    p = Process(target=obj.explain)

    p.start()

    obj.v = 999
    obj.explain()
