import proto.code_eval_pb2 as code_eval
import subprocess
import grpc
import sys
import time

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

    results = test(code, tests)

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
    return reply.err_msg


# Print how to start program via command-line
def printUsage():
    print("Usage: python %s <code.py> <tests.json>" % sys.argv[0])


# Run program if run as main
if __name__ == "__main__":
    serve()
