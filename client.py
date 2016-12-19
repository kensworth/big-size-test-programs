import proto.code_eval_pb2 as code_eval
import subprocess
import grpc
import sys
import time
import boto3
import json

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

            tests, ok = check_testcases(tests)
            if ok == False:
                print("Got bad test case: %s" % tests)

                return_queue.send_message(MessageBody="Response", MessageAttributes={
                    'ID': {
                        'DataType': 'String',
                        'StringValue': 'tempId'
                    },
                    'Success':{
                        'DataType': 'Number',
                        'StringValue': "0"
                    },
                    'ErrorMessage':{
                        'DataType': 'String',
                        'StringValue': "Bad test case"
                    },
                })
                
                message.delete()
                continue

            results = test(code, tests)
            print(results.failed_case)

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


def check_testcases(testcases):
    if testcases == None:
        return testcases, False

    tests_json = json.loads(testcases)
    if "program_name" not in tests_json or \
        "tests" not in tests_json:
        return testcases, False

    if "call_signature" not in tests_json:
        tests_json["call_signature"] = ""

    prog_name = tests_json["program_name"]
    if isinstance(prog_name, str):
        return testcases, False
    if " " in prog_name:
        return testcases, False

    call_sig = tests_json["call_signature"]
    if isinstance(call_sig, str):
        return testcases, False
    call_sig_arr = [arg.strip() for arg in call_sig.split(',') if arg.strip() != ""]
    for arg in call_sig_arr:
        if " " in arg:
            return testcases, False

    tests = tests_json["tests"]
    if type(tests) != list:
        return testcases, False

    for test in tests:
        if len(call_sig_arr) == 0 and "input" not in test:
            test["input"] = {}
        if "expected" not in test or "input" not in test:
            return testcases, False
        inputs = test["input"]
        if type(inputs) != dict:
            print("0")
            return testcases, False
        args = inputs.keys()
        if len(args) != len(call_sig_arr):
            return testcases, False
        for arg in args:
            if arg.strip() not in call_sig_arr:
                return testcases, False

    return json.dumps(tests_json), True


def test(code, tests):
    # Connect to server
    channel = grpc.insecure_channel('%s:%d' % (address, port))
    stub = code_eval.CodeEvaluatorStub(channel)

    # Form request
    request = code_eval.EvalRequest()
    request.code = code
    request.test_cases = tests

    # Query the server
    try:
        reply = stub.Eval(request)
    except:
        reply = code_eval.EvalReply(success=False, err_msg="RPC error")

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
