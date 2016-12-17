import proto.code_eval_pb2 as code_eval
import subprocess
import grpc
import sys
import time
import boto3

address = "localhost"
port = 8000

sqs_url = "https://sqs.us-east-1.amazonaws.com/542342679377/SubmissionQueue"
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName='SubmissionQueue')

def serve():
    start_docker()

    while True:
        print("Waiting for message...")
        for message in queue.receive_messages(
            MessageAttributeNames=['Submission'],
            WaitTimeSeconds=20
        ):
            print("Received message")
            code = ''
            if message.message_attributes is not None:
                code = message.message_attributes.get('Submission').get('StringValue')

            print('Got code: {0}'.format(code))

            test(code)

            # Let the queue know that the message is processed
            message.delete()

            start_docker()


def start_docker():
    # Run ./scripts/run_docker.sh
    p = subprocess.Popen(["sh", "scripts/run_docker.sh"]).wait()
    time.sleep(1)

def test(code):
    # Connect to server
    channel = grpc.insecure_channel('%s:%d' % (address, port))
    stub = code_eval.CodeEvaluatorStub(channel)

    # Form request
    request = code_eval.EvalRequest()
    request.code = code

    # Query the server
    reply = stub.Eval(request)

    # Print the response
    print(reply.response)


# Print how to start program via command-line
def printUsage():
    print("Usage: python %s \"def fib(n): ...\"" % sys.argv[0])


# Run program if run as main
if __name__ == "__main__":
    serve()
