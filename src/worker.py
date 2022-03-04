import redis
import os
import traceback
import sys
import json
import time
from random import randint
from kjk.allocation import Allocator
from kjk.inputdata import RedisDataprovider
from kjk.logging import clog
from kjk.mail import KjKEmailclient

SAVE_JOB_DATA = True


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
        self.r = redis.StrictRedis(
            host=os.getenv("REDIS_HOST"),
            port=os.getenv("REDIS_PORT"),
            db=0,
            password=os.getenv("REDIS_PASSWORD"),
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

        # store input in REDIS for 30 secs
        # to grab the input for debugging
        self.r.set(f"JOB_{job_id}", job_res)
        self.r.expire(f"JOB_{job_id}", 10 * 60)

        job = json.loads(job_res)
        start = time.time()
        data = job["data"]
        if SAVE_JOB_DATA:
            f = open("job.json", "w")
            json.dump(data, f, indent=4)
            f.close()
        dp = RedisDataprovider(job["data"])
        a = Allocator(dp)
        output = a.get_allocation()

        # store results in REDIS for 10 min
        json_result = json.dumps(output)
        self.r.set(f"RESULT_{job_id}", json_result)
        self.r.expire(f"RESULT_{job_id}", 10 * 60)

        # store logs in REDIS for 10 min
        log_result = json.dumps(clog.get_logs())
        self.r.set(f"LOGS_{job_id}", log_result)
        self.r.expire(f"LOGS_{job_id}", 10 * 60)

        email_client = KjKEmailclient()
        email_text = ""
        for log_line in clog.get_logs():
            if log_line["level"] in ("ERROR"):
                email_text += log_line["message"] + "\n"
        email_client.send_mail(email_text)

        clog.purge()
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
            error_str = traceback.format_exc()
            print("-" * 60)

            # store error in REDIS for 10 min
            error_id = randint(10000, 99999)
            json_result = json.dumps(
                {
                    "error": "Sorry, er is een fout opgetreden in deze indeling.",
                    "error_id": f"{error_id}",
                    "job_id": f"{job_id}",
                }
            )
            self.r.set(f"RESULT_{job_id}", json_result)
            self.r.expire(f"RESULT_{job_id}", 10 * 60)
            self.r.set(f"ERROR_{error_id}", error_str)
            self.r.expire(f"ERROR_{error_id}", 24 * 60 * 60)

            self.r.sadd(self.failed, job_id)
            self.r.hdel(self.jobs, job_id)
            self.r.lrem(self.active, 0, job_id)
        self.wait_for_jobs()


if __name__ == "__main__":
    d = JobDispatcher()
    d.wait_for_jobs()
