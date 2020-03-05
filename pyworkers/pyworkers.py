from threading import Thread
from multiprocessing import Process, Queue
import traceback
import sys
import logging
from logging import handlers
from queue import Empty
import os


class ThreadWorkers:
    def __init__(self, worker=1, interval=1.0, logger=None):
        self.is_running = True
        self.logger = logger
        self._updating_threads = [Thread(target=self.loop) for _ in range(worker)]
        self.tasks = list()
        self.results = list()
        self.interval = interval
        [t.start() for t in self._updating_threads]

    def _log(self, msg):
        if self.logger is None:
            print(msg)
            traceback.print_last(file=sys.stderr)
        else:
            self.logger.exception(msg)

    def loop(self):
        while self.is_running:
            try:
                function, args = self.tasks.pop(0)
                result = function(*args)
                if result is not None:
                    self.results.append(result)
            except IndexError:
                pass
            except Exception as e:
                self._log(f"Unhandled exception {e}")

    def add_task(self, func, args):
        self.tasks.append((func, args))

    def get_result(self):
        try:
            return self.results.pop(0)
        except IndexError:
            return None

    def stop(self):
        self.is_running = False

    def release(self):
        [t.join() for t in self._updating_threads]


class Listener:
    def __init__(self):
        self.msg_queue = Queue()
        self.process = Process(target=self.listener_process, args=(self.msg_queue, self.listener_configurer))
        self.process.daemon = True
        self.process.start()

    @staticmethod
    def listener_configurer():
        logger = logging.getLogger("Listener")
        h = handlers.RotatingFileHandler('app.log', 'a', 1024, 10)
        f = logging.Formatter('%(asctime)s %(levelname)-8s  %(name)s %(processName)-10s %(message)s')
        h.setFormatter(f)
        logger.addHandler(h)
        logger.setLevel(logging.DEBUG)
        logger.info(f"Listener initiated")

    @staticmethod
    def listener_process(queue, configurer):
        configurer()
        for record in iter(queue.get, 'STOP'):
            try:
                logger = logging.getLogger(record.name)
                logger.handle(record)  # No level or filter logic applied - just do it!
            except Exception:
                import sys, traceback
                print('Whoops! Problem:', file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

    def stop(self):
        self.msg_queue.put('STOP')

    def release(self):
        self.process.join()


class ProcessWorkers:
    def __init__(self, number_of_workers, logging_queue):
        self.number_of_workers = number_of_workers
        self._input_queue = Queue()
        self._output_queue = Queue()
        self._logging_queue = logging_queue
        self.processes = [Process(
            target=self.loop,
            args=(self._input_queue, self._output_queue, self._logging_queue, self.worker_configurer)
        ) for _ in range(self.number_of_workers)]
        for p in self.processes:
            p.daemon = True
            p.start()

    @staticmethod
    def worker_configurer(queue):
        h = handlers.QueueHandler(queue)  # Just the one handler needed
        logger = logging.getLogger("Listener")
        logger.addHandler(h)
        # send all messages, for demo; no other level or filter logic applied.
        logger.setLevel(logging.DEBUG)
        logger.info(f"Worker initiated")

    @staticmethod
    def loop(input_queue, output_queue, logging_queue, worker_configurer):
        worker_configurer(logging_queue)
        logger = logging.getLogger("Listener")
        for func, args in iter(input_queue.get, 'STOP'):
            try:
                output = func(*args)
                output_queue.put(output)
            except Exception as e:
                logger.exception(e)

    def add_task(self, func, args):
        self._input_queue.put_nowait((func, args))

    def get_result(self):
        try:
            return self._output_queue.get_nowait()
        except Empty:
            return None

    def stop(self):
        [self._input_queue.put('STOP') for _ in range(self.number_of_workers)]

    def release(self):
        for p in self.processes:
            p.join()
