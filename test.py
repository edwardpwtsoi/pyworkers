from pyworkers import Listener, ProcessWorkers
import time


def foo(a, b):
    return a / b


if __name__ == "__main__":
    l = Listener()
    ps = ProcessWorkers(2, l.msg_queue)
    [ps.add_task(foo, (x, y)) for x, y in zip([1, 2, 3], [4, 5, 6])]
    count = 0
    while count < 3:
        result = ps.get_result()
        if result is not None:
            print(result)
            count += 1
    ps.add_task(foo, (1, 0))  # create a zero division error check log file to see listener is logging correctly
    time.sleep(1)  # wait for task done
    l.stop()
    ps.stop()
    l.release()
    ps.release()
