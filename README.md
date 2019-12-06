# cnd

```
usage: client.py [-h] [-n INSTANCES] [-d DIFFICULTY] [-t TIMEOUT]

Cloud nonce discovery

optional arguments:
  -h, --help            show this help message and exit
  -n INSTANCES          Number of VMs to spawn
  -d DIFFICULTY, --difficulty DIFFICULTY
                        Difficulty (number of leading zeroes) for the nonce
                        discovery algorithm
  -t TIMEOUT, --timeout TIMEOUT
                        Maximum time spent in seconds.
```

## Pre-requisites
* Python 3
* Boto3: `pip install boto3`
* An AWS account

## Setting up:
* Create a role at https://console.aws.amazon.com/iam/home?region=us-west-1#/roles with the permission `AmazonSQSFullAccess`. This role also __needs__ to named `instance`.
* Create a group at https://console.aws.amazon.com/iam/home?region=us-west-1#/groups with the permissions `AmazonEC2FullAccess`, `AmazonSQSFullAccess` and `IAMFullAccess`
* Create an user at https://console.aws.amazon.com/iam/home?region=us-west-1#/users with belonging to the group you've just created.
* Place the AWS credentials that were just generated in `~/.aws/credentials`, the file should look like this:

```
[default]
aws_access_key_id=...
aws_secret_access_key=...

region=us-west-1
```
(notice the `region=us-west-1` which is necessary, although you can edit `instance.py` on line 7 to match your desired region if wanted)

* Run `client.py` with parameters `-n` and `-d`
* Sit back and enjoy :)
