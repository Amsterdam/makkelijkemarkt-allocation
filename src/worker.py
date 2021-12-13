import redis
import traceback
import sys
import json
import time
from kjk.allocation import Allocator
from kjk.inputdata import FixtureDataprovider


class JobDispatcher:
    """
    This object integrates with the bee queue npm package
    it will get incomming jobs from the KjK application and
    assign a python worker for the allocation job

    Bee Queue keys:
    kjk-alloc:allocation:id -> string
    kjk-alloc:allocation:waiting -> list
    kjk-alloc:allocation:active -> list
    kjk-alloc:allocation:failed -> set
    kjk-alloc:allocation:succeeded -> set
    kjk-alloc:allocation:jobs -> hash

    see: https://github.com/bee-queue/bee-queue

    """

    def __init__(self):
        REDIS_HOST = "127.0.0.1"
        REDIS_PORT = 6379
        REDIS_PASSWORD = "Salmagundi"
        self.r = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            password=REDIS_PASSWORD,
            charset="utf-8",
            decode_responses=True,
        )
        self.waiting = "kjk-alloc:allocation:waiting"
        self.active = "kjk-alloc:allocation:active"
        self.jobs = "kjk-alloc:allocation:jobs"
        self.success = "kjk-alloc:allocation:succeeded"
        self.failed = "kjk-alloc:allocation:failed"

    def list_keys(self):
        keys = self.r.keys()
        for k in keys:
            key_type = self.r.type(k)
            print(k, " -> ", key_type)

    def process_job(self, job_id):
        print("processing .....")
        job_res = self.r.hget(self.jobs, job_id)
        job = json.loads(job_res)
        print(job)
        start = time.time()
        dp = FixtureDataprovider("../fixtures/dapp_20211030/a_input.json")
        a = Allocator(dp)
        output = a.get_allocation()
        json_result = json.dumps(output)
        self.r.set(f"RESULT_{job_id}", json_result)
        stop = time.time()
        print("Concept allocation completed in ", round(stop - start, 2), "sec")

    def wait_for_jobs(self):
        print("waiting for allocation jobs...")
        # self.list_keys()
        job_id = self.r.brpoplpush(self.waiting, self.active)
        try:
            self.process_job(job_id)
            self.r.sadd(self.success, job_id)
            self.r.lrem(self.active, 0, job_id)
            self.r.hdel(self.jobs, job_id)
        except Exception as e:
            print("Error: ", e)
            print("-" * 60)
            traceback.print_exc(file=sys.stdout)
            print("-" * 60)
            self.r.sadd(self.failed, job_id)
            self.r.hdel(self.jobs, job_id)
            self.r.lrem(self.active, 0, job_id)
        self.wait_for_jobs()


if __name__ == "__main__":
    d = JobDispatcher()
    d.wait_for_jobs()
