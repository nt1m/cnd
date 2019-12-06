import boto3
import argparse
import math
import json
from time import sleep
from datetime import datetime
import signal
import sys

ec2 = boto3.resource("ec2")
sqs = boto3.resource("sqs")

## Initialization
script = open("instance.py", "r").read()

def create_instances(number_vms):
    return ec2.create_instances(
        UserData=script,
        ImageId="ami-02e8790767f496602",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=number_vms,
        IamInstanceProfile={
            "Name": "instance"
        }
    )

def create_or_get_queue(name):
    try:
        q = sqs.get_queue_by_name(
            QueueName=name
        )
        print("Found queue for", name)
        q.purge()
        print("Finished purging", name)
        sleep(60)
        return q
    except:
        print("Creating queue for", name)
        return sqs.create_queue(
            QueueName=name,
            Attributes={
                "FifoQueue": "true",
                "ContentBasedDeduplication": "true"
            },
        )

## Receive messages helper
def receive_messages(queue, n_messages=1):
    messages = []
    while len(messages) < n_messages:
        messages = queue.receive_messages(
            MaxNumberOfMessages=n_messages
        )
    return messages


shutdown_data = {
    "instances": list(),
    "input_queue": None,
    "output_queue": None,
}

## Main
def main(number_vms=5, difficulty=32, timeout=None):
    if timeout != None:
        signal.alarm(timeout)

    epoch = datetime.utcfromtimestamp(0)
    start_time = (datetime.now() - epoch).total_seconds()
    max_nonce=2**32
    input_queue = create_or_get_queue("input_queue.fifo")
    shutdown_data["input_queue"] = input_queue

    output_queue = create_or_get_queue("output_queue.fifo")
    shutdown_data["output_queue"] = output_queue

    instances = create_instances(number_vms)
    shutdown_data["instances"] = instances

    print("Started", number_vms, "instances")

    # split out the tasks
    batch_size = math.ceil(max_nonce / number_vms)
    batches = [
        [i, min(i+batch_size, max_nonce)-1]
        for i in range(0, max_nonce, batch_size)
    ]
    print("Split in", batches)

    # send out messages to input queue
    for i in range(len(batches)):
        message = {
            "min": batches[i][0],
            "max": batches[i][1],
            "difficulty": difficulty,
        }

        input_queue.send_message(
            MessageBody=json.dumps(message),
            MessageGroupId="input_queue"
        )

    print("Finished sending messages")

    # wait 4 message
    messages = receive_messages(output_queue, 1)
    print("Got message", messages)

    body = json.loads(messages[0].body)
    end_time = (datetime.now() - epoch).total_seconds()

    print("The golden nonce is:", body["golden_nonce"])
    print("The golden hash is:", body["golden_hash"])
    print("Cloud start time:", body["start_time"])
    print("Cloud end time:", body["end_time"])

    print("start time:", start_time)
    print("end time:", end_time)

    print("Cloud overhead:", (body["start_time"] - start_time) + (end_time - body["end_time"]))
    print("Cloud delta time:", body["end_time"] - body["start_time"])

    # clean up
    cleanup(instances, input_queue, output_queue);


## scram/cleanup
def cleanup(instances, input_q, output_q):
    print("Cleaning up");
    # terminate instances
    for instance in instances:
        instance.terminate()

    # terminate queues
    input_q.delete()
    output_q.delete()

def scram(signal, stack_frame):
    print("Signal found:", signal)
    cleanup(
        shutdown_data["instances"],
        shutdown_data["input_queue"],
        shutdown_data["output_queue"]
    )
    sys.exit(0)

signal.signal(signal.SIGINT, scram)
signal.signal(signal.SIGALRM, scram)


## Argument parser
parser = argparse.ArgumentParser(description="Cloud nonce discovery")
parser.add_argument("-n", type=int, dest="instances", default=1, help="Number of VMs to spawn")
parser.add_argument("-d", "--difficulty", type=int, default=6, help="Difficulty (number of leading zeroes) for the nonce discovery algorithm")
parser.add_argument("-t", "--timeout", type=int, default=None, help="Maximum time spent in seconds.")

args = parser.parse_args()

main(args.instances, args.difficulty, args.timeout)
