import proto.code_eval_pb2 as code_eval
import subprocess
import grpc
import sys
import time
import boto3

address = "localhost"
port = 8000

sqs_url = "https://sqs.us-east-1.amazonaws.com/542342679377/SubmissionQueue"
sqs_return_url = "https://sqs.us-east-1.amazonaws.com/542342679377/ReturnQueue"
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName='SubmissionQueue')
return_queue = sqs.get_queue_by_name(QueueName = 'ReturnQueue')

def serve():
    start_docker()

    while True:
        print("Waiting for message...")
        for message in queue.receive_messages(
            MessageAttributeNames=['Submission', 'Tests'],
            WaitTimeSeconds=20
        ):
            print("Received message")

            code = ''
            tests = ''
            if message.message_attributes is not None:
                msgSubmission = message.message_attributes.get('Submission')
                if msgSubmission is not None:
                    code = msgSubmission.get('StringValue')
                msgTests = message.message_attributes.get('Tests')
                if msgTests is not None:
                    tests = msgTests.get('StringValue')
                else:
                    f = open('test/testcases.json', 'r')
                    tests = f.read()
                    f.close()

            print('Got code: {0}'.format(code))
            print('Got tests: {0}'.format(tests))

            results = test(code, tests)

            return_queue.send_message(MessageBody="Response", MessageAttributes={
                'ID': {
                    'DataType': 'String',
                    'StringValue': 'tempId'
                },
                'Success':{
                    'DataType': 'Number',
                    'StringValue': ("1" if results.success else "0")
                },
                'ErrorMessage':{
                    'DataType': 'String',
                    'StringValue': (results.err_msg if results.err_msg != "" else "N/A")
                },
                'TimeTaken':{
                    'DataType': 'Number',
                    'StringValue': str(results.time_taken)
                },
                'FailedCase':{
                    'DataType': 'String',
                    'StringValue': (results.failed_case if results.failed_case != "" else "{}")
                } 
            })

            # Let the queue know that the message is processed
            message.delete()

            start_docker()

def start_docker():
    # Run ./scripts/run_docker.sh
    p = subprocess.Popen(["sh", "scripts/run_docker.sh"]).wait()
    time.sleep(1)

def test(code, tests):
    # Connect to server
    channel = grpc.insecure_channel('%s:%d' % (address, port))
    stub = code_eval.CodeEvaluatorStub(channel)

    # Form request
    request = code_eval.EvalRequest()
    request.code = code
    request.test_cases = tests

    # Query the server
    reply = stub.Eval(request)

    # Print the response
    print(reply.err_msg)
    return reply


# Print how to start program via command-line
def printUsage():
    print("Usage: python %s \"def fib(n): ...\"" % sys.argv[0])


# Run program if run as main
if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        exit(0)
