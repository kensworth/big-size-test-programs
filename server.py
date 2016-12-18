import proto.code_eval_pb2 as code_eval
import concurrent.futures as futures
import os
import grpc
import time
import random
import subprocess
import json

# Our service's address
address = "[::]"
port = 8000


# Template for generated .py file
test_fn = "test.py"
python_template = '''%s
import sys
import json
import os
if __name__ == "__main__":
    try:
        test = json.loads(sys.argv[1])
        input_values = test["input"]
        expected_output = test["expected"]
        ret = %s(**input_values)
        parent_fd = int(sys.argv[2])
        if ret == expected_output:
            os.write(parent_fd, "Test case passed.")
            sys.exit(0)
        else:
            os.write(parent_fd, "%%s" %% ret)
            sys.exit(1)
    except Exception as e:
        import inspect
        frame = inspect.trace()[-1]
        os.write(parent_fd, "Line %%d: %%s: %%s" %% (frame[2], type(e).__name__, e))
        sys.exit(1)
'''



def run_test_case(test_case):
    in_fd, out_fd = os.pipe()

    start = time.time()
    p = subprocess.Popen(["python", test_fn, test_case, str(out_fd)])
    stdout, stderr = p.communicate()
    end = time.time()
    time_taken = (end - start) * 1000

    result = os.read(in_fd, 1024)

    os.close(in_fd)
    os.close(out_fd)

    rc = p.returncode

    return rc, time_taken, result, stdout

def run_all_test_cases(test_cases, code):
    failed_cases = []
    time_taken = 0
    for ind, test_case in enumerate(test_cases):
        json_case = json.dumps(test_case)
        rc, time, result, stdout = run_test_case(json_case)
        time_taken += time
        if rc != 0:
            failed_cases.append((ind, result))
    return failed_cases, time_taken

def parse_test_results(test_cases, failed_cases):
    if not failed_cases:
        res = 'All test cases passed!'
        return True, res, None

    first_fail = failed_cases[0]
    fail_info = test_cases[first_fail[0]]
    fail_info["output"] = first_fail[1]
    res = 'Test case failed.\nInput: %s\nExpected: %s\nGot: %s' % \
        (str(json.dumps(fail_info["input"])), fail_info["expected"], fail_info["output"])
    fail_info_json = json.dumps(fail_info)
    return False, res, fail_info_json


class CodeEvaluatorServicer(code_eval.CodeEvaluatorServicer):
    def Eval(self, request, context):
        try:
            tests_json = json.loads(request.test_cases)
        except Exception:
            return code_eval.EvalReply(success=False)

        tests = tests_json["tests"]
        prog_name = tests_json["program_name"]
        code = request.code

        write_to_file(test_fn, prog_name, code)
        failed_tests, time_taken = run_all_test_cases(tests, code)
        success, err_msg, failed_case = parse_test_results(tests, failed_tests)
        return code_eval.EvalReply(success=success, err_msg=err_msg, time_taken=time_taken, failed_case=failed_case)


def write_to_file(filename, prog_name, code):
    content = python_template % (code, prog_name)
    f = open(filename, 'w')
    f.write(content)
    f.close()

def delete_file(filename):
    os.remove(filename)


# Serve the service on the address:port
def serve():
    # Create server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    code_eval.add_CodeEvaluatorServicer_to_server(CodeEvaluatorServicer(), server)
    server.add_insecure_port('%s:%d' % (address, port))

    # Start the server
    server.start()

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)

# Run program if run as main
if __name__ == "__main__":
    serve()
