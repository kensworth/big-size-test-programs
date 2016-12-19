import proto.code_eval_pb2 as code_eval
import subprocess
import grpc
import sys
import time
import json

address = "localhost"
port = 8000

def serve():
    if len(sys.argv) < 3:
        printUsage()
        return

    fn1 = sys.argv[1]
    f1 = open(fn1, 'r')
    code = f1.read()
    f1.close()

    fn2 = sys.argv[2]
    f2 = open(fn2, 'r')
    tests = f2.read()
    f2.close()

    tests, ok = check_testcases(tests)
    if ok == True:
        print(tests)
        print "OK"
    if ok == False:
        print "Not OK"

    #results = test(code, tests)

def start_docker():
    # Run ./scripts/run_docker.sh
    p = subprocess.Popen(["sh", "scripts/run_docker.sh"]).wait()
    time.sleep(1)

def check_testcases(testcases):
    if testcases == None:
        return testcases, False

    tests_json = json.loads(testcases)
    if "program_name" not in tests_json or \
        "call_signature" not in tests_json or \
        "tests" not in tests_json:
        return testcases, False

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
    reply = stub.Eval(request)

    # Print the response
    print(reply.err_msg)
    return reply.err_msg


# Print how to start program via command-line
def printUsage():
    print("Usage: python %s <code.py> <tests.json>" % sys.argv[0])


# Run program if run as main
if __name__ == "__main__":
    serve()
