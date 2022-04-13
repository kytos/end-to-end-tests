import os
import sys
import time
from pymongo import MongoClient
from pymongo.errors import OperationFailure, AutoReconnect


def mongo_client(
    host_seeds=os.environ.get("MONGO_HOST_SEEDS"),
    username=os.environ.get("MONGO_USERNAME"),
    password=os.environ.get("MONGO_PASSWORD"),
    database=os.environ.get("MONGO_DBNAME"),
    connect=False,
    retrywrites=True,
    retryreads=True,
    readpreference="primaryPreferred",
    maxpoolsize=int(os.environ.get("MONGO_MAX_POOLSIZE", 6)),
    minpoolsize=int(os.environ.get("MONGO_MIN_POOLSIZE", 3)),
    serverselectiontimeoutms=30000,
    **kwargs,
) -> MongoClient:
    """mongo_client."""
    return MongoClient(
        host_seeds.split(","),
        username=username,
        password=password,
        connect=False,
        authsource=database,
        retrywrites=retrywrites,
        retryreads=retryreads,
        readpreference=readpreference,
        maxpoolsize=maxpoolsize,
        minpoolsize=minpoolsize,
        **kwargs,
    )


def mongo_hello_wait(mongo_client=mongo_client, retries=10, timeout_ms=10000):
    """Wait for MongoDB."""
    try:
        client = mongo_client(serverselectiontimeoutms=timeout_ms)
        print("Trying to run 'hello' command on MongoDB...")
        client.db.command("hello")
        print("Ran 'hello' command on MongoDB successfully. It's ready!")
    except (OperationFailure, AutoReconnect) as exc:
        retries -= 1
        if retries > 0:
            time.sleep(max(timeout_ms / 1000, 1))
            return mongo_hello_wait(mongo_client, retries, timeout_ms)
        print(f"Maximum retries reached when waiting for MongoDB. {str(exc)}")
        sys.exit(1)


if __name__ == "__main__":
    print("Trying to run hello command on MongoDB...")
    retries = 5
    if len(sys.argv) > 1:
        retries = int(sys.argv[1])

    mongo_hello_wait(retries=retries)
