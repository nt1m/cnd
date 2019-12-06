#!/usr/bin/env python
from hashlib import sha256
import boto3
import json
from datetime import datetime

boto3.setup_default_session(region_name="us-west-1")
sqs = boto3.resource("sqs")

base_block = "COMSM0010cloud"

def get_final_hash(block):
    hash = get_sha256_hash(get_sha256_hash(block))
    hash_in_binary = str(bin(int("1" + hash, 16))[3:])
    return hash_in_binary

def get_sha256_hash(block):
    obj = sha256(block.encode("utf-8"))
    return obj.hexdigest()

def is_golden_nonce(difficulty, hash):
    i = 0
    while i < difficulty:
        if hash[i] != "0":
            return False
        i += 1
    return True

def compute_hash_for_nonce(nonce):
    block = base_block + str(nonce)
    hash = get_final_hash(block)
    return hash

def receive_messages(queue, n_messages=1):
    messages = []
    while len(messages) < n_messages:
        messages = queue.receive_messages(
            MaxNumberOfMessages=n_messages
        )
    return messages

def main():
    # read message from queue
    input_queue = sqs.get_queue_by_name(
        QueueName="input_queue.fifo"
    )
    output_queue = sqs.get_queue_by_name(
        QueueName="output_queue.fifo"
    )
    messages = receive_messages(input_queue, 1)
    # print("Got message")

    message = messages[0]
    body = json.loads(message.body)
    # print(body)
    input_queue.delete_messages(Entries=[{
        "Id": message.message_id,
        "ReceiptHandle": message.receipt_handle
    }])

    start_time = datetime.now()

    # print("Deleted message")

    # Use a while loop because creating a range with large numbers causes a MemoryError
    i = body["min"]
    max = body["max"]
    difficulty = body["difficulty"]
    found = False
    while i < max:
        hash = compute_hash_for_nonce(i)

        # if nonce is correct, send back message to output queue, and stop program
        if is_golden_nonce(difficulty, hash):
            print("Found golden nonce")
            end_time = datetime.now()
            epoch = datetime.utcfromtimestamp(0)
            output_queue.send_message(
                MessageBody=json.dumps({
                    "golden_nonce": i,
                    "golden_hash": hash,
                    "start_time": (start_time - epoch).total_seconds(),
                    "end_time": (end_time - epoch).total_seconds()
                }),
                MessageGroupId="output_queue"
            )
            found = True
            break
        i += 1

    if not found:
        print("Couldn't find golden nonce")

# def main():
#     difficulty = 32
#     i = 0
#     min = 0
#     max = 2**32
#     while i < max:
#         nonce = compute_nonce(i)
#
#         # if nonce is correct, send back message to output queue, and stop program
#         if is_golden_nonce(difficulty, nonce):
#             print("Found golden nonce")
#             print({
#                     "golden_number": i,
#                     "golden_nonce": nonce,
#             })
#             break
#         i += 1

main()
