import boto3

sqs_url = "https://sqs.us-east-1.amazonaws.com/542342679377/SubmissionQueue"

sqs = boto3.resource('sqs')

# Get the queue
queue = sqs.get_queue_by_name(QueueName='SubmissionQueue')

for message in queue.receive_messages():
    # Print out the body and author (if set)
    print('Hello, {0}'.format(message.body))

    # Let the queue know that the message is processed
    message.delete()
