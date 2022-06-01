"""
This is the main script that starts everything.
"""
from multiprocessing import Process
import time

import uvicorn

from modules.worker.main import Worker
from settings import DATASTORE_APP_ADDRESS

def run_worker_app_process():
    """
    start the worker application as a process
    """
    worker_app_proc = Process(target=Worker)
    worker_app_proc.start()
    return worker_app_proc

def run_storage_app(address, port):
    """
    start the storage application with uvicorn
    """
    uvicorn.run("modules.datastore.main:app", host=address,
                port=port, log_level="critical")

def run_storage_app_process(address, port):
    """
    run storage app as a process
    """
    storage_app_proc = Process(target=run_storage_app, args=(address, port))
    storage_app_proc.start()
    return storage_app_proc


if __name__ == "__main__":
    run_storage_app_process(*DATASTORE_APP_ADDRESS)
    run_worker_app_process()

    while True:
        time.sleep(10)
