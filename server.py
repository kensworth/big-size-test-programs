import proto.code_eval_pb2 as code_eval
import concurrent.futures as futures
import os
import grpc
import time
import random
import subprocess32 as subprocess
import json
import signal

# Our service's address
address = "[::]"
port = 8000


# Template for generated .py file
test_fn = "test.py"
python_template = '''%s

import sys
import json
import os
import inspect
import time
if __name__ == "__main__":
    parent_fd = int(sys.argv[2])
    try:
        test = json.loads(sys.argv[1])
        input_values = test["input"]
        expected_output = test["expected"]
        start = time.time()
        ret = %s(**input_values)
        end = time.time()
        time_taken = (end - start) * 1000
        if parent_fd == None:
            sys.exit(0)
        if ret == expected_output:
            os.write(parent_fd, "%%d\\n" %% time_taken)
            os.write(parent_fd, "Test case passed.")
            sys.exit(0)
        else:
            os.write(parent_fd, "%%d\\n" %% time_taken)
            os.write(parent_fd, "%%s" %% ret)
            sys.exit(2)
    except Exception as e:
        frame = inspect.trace()[-1]
        os.write(parent_fd, "0\\n")
        os.write(parent_fd, "Line %%d: %%s: %%s" %% (frame[2], type(e).__name__, e))
        sys.exit(2)
'''



def run_test_case(test_case):
    in_fd, out_fd = os.pipe()

    print(["python", test_fn, test_case, str(out_fd)])

    try:
        process = subprocess.Popen(["python", test_fn, test_case, str(out_fd)], stdout=subprocess.PIPE, preexec_fn=os.setsid, close_fds=False)
    except:
        print("Error")
        os.close(in_fd)
        os.close(out_fd)
        return 1, 0, "Fatal error.", ""

    print("Program started")

    try:
        stdout, stderr = process.communicate(timeout=6)
    except subprocess.TimeoutExpired:
        print("Timeout: %d" % process.pid)
        try:
            os.killpg(process.pid, signal.SIGINT)
        except:
            print("Error: no process %d" % process.pid)

        stdout, stderr = process.communicate()
        os.close(in_fd)
        os.close(out_fd)

        return 1, 0, "Time Limit Exceeded.", stdout
    except:
        print("Error")
        os.close(in_fd)
        os.close(out_fd)
        return 1, 0, "Error", ""

    rc = process.returncode
    print("Program finished, error code: %d" % rc)
    if rc == 1:
        print("Syntax error")
        os.close(in_fd)
        os.close(out_fd)
        return rc, 0, "Syntax error", ""

    result = os.read(in_fd, 1024)
    time_taken_str = result[:result.index('\n')]
    result = result[result.index('\n')+1:]
    time_taken = float(time_taken_str)
    print("time taken: %s" % time_taken_str)
    print("result: %s" % result)

    os.close(in_fd)
    os.close(out_fd)

    return rc, time_taken, result, stdout

def run_all_test_cases(test_cases, code):
    failed_cases = []
    time_taken = 0
    for ind, test_case in enumerate(test_cases):
        json_case = json.dumps(test_case)
        rc, time, result, stdout = run_test_case(json_case)
        time_taken += time
        if rc != 0:
            failed_cases.append((ind, result, stdout))
    return failed_cases, time_taken

def parse_test_results(test_cases, failed_cases):
    if not failed_cases:
        res = 'All test cases passed!'
        return True, res, None

    first_fail = failed_cases[0]
    fail_info = test_cases[first_fail[0]]
    fail_info["output"] = first_fail[1]
    fail_info["stdout"] = first_fail[2]
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
    print(content)
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
