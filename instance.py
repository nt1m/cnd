#!/usr/bin/env python
from hashlib import sha256
import boto3
import json

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

def compute_nonce(number):
    block = base_block + str(number)
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
    print("Got message")

    message = messages[0]
    body = json.loads(message.body)
    print(body)
    input_queue.delete_messages(Entries=[{
        "Id": message.message_id,
        "ReceiptHandle": message.receipt_handle
    }])

    print("Deleted message")

    # Use a while loop because creating a range with large numbers causes a MemoryError
    i = body["min"]
    max = body["max"]
    difficulty = body["difficulty"]
    while i < max:
        nonce = compute_nonce(i)

        # if nonce is correct, send back message to output queue, and stop program
        if is_golden_nonce(difficulty, nonce):
            print("Found golden nonce")
            output_queue.send_message(
                MessageBody=json.dumps({
                    "golden_number": i,
                    "golden_nonce": nonce,
                }),
                MessageGroupId="output_queue"
            )
            break
        i += 1

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
