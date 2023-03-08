from threading import Thread, Semaphore, Barrier, current_thread
import time
import random

num_steps = 3
num_ep_threads = 2

sem0 = Semaphore(1)
barrier_0 = Barrier(num_ep_threads + 1)
barrier_1 = Barrier(num_ep_threads + 1)

def VCWG():
    for step in range(num_steps):
        sem0.acquire()
        print(f"VCWG: Uploading weather for time step {step + 1}...")
        time.sleep(1)
        barrier_0.wait()

        barrier_1.wait()
        print(f"VCWG: Downloading energy for time step {step + 1}...")
        time.sleep(1)
        sem0.release()

def ep():
    while True:
        barrier_0.wait()
        print(f"EP-{current_thread().name}: Downloading weather for time step...")
        time.sleep(random.randint(1, 3))
        print(f"EP-{current_thread().name}: Uploading energy for time step...")
        time.sleep(random.randint(1, 3))
        barrier_1.wait()

if __name__ == '__main__':
    VCWG_thread = Thread(target=VCWG)
    VCWG_thread.start()
    # Create EP threads
    threads = []
    for i in range(num_ep_threads):
        thread = Thread(target=ep, name=i)
        threads.append(thread)
        thread.start()

    # Wait for VCWG and EP threads to complete
    VCWG_thread.join()
    for thread in threads:
        thread.join()



    # Wait for VCWG and EP threads to complete
    VCWG_thread.join()
    for thread in threads:
        thread.join()
