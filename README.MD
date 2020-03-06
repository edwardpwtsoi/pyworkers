# Different kinds of consumer worker implementation

### Introduction:
This repository is developed as a package for having long living processes to share I/O bound and CPU bound task. 


### Usage
```python
class ThreadWorkers:
    def __init__(self, worker=1, interval=1.0, logger=None):return None
    def add_task(self, func, args): return None
    def get_result(self): return func(args)
    def stop(self): return None
    def release(self): return None
    

class Listener:
    def __init__(self):return None
    def stop(self): return None
    def release(self): return None
    

class ProcessWorkers:
    def __init__(self, number_of_workers, logging_queue):return None
    def add_task(self, func, args): return None
    def get_result(self): return func(args)
    def stop(self): return None
    def release(self): return None
```


### Example script:
```python
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
```

### TODO:

- Documentation
- Publish to PYPI
