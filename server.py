import proto.code_eval_pb2 as code_eval
import concurrent.futures as futures
import os
import grpc
import time
import random
import subprocess

# Our service's address
address = "[::]"
port = 8000

# Test cases, hard-code for now
test_fn = "test.py"
prog_name = "fib"
prog_call_sig = [int]
prog_ret_sig = [int]
test_cases = {
    1: 1,
    2: 1,
    3: 2,
    4: 3,
    5: 5,
    6: 8
}

# Template for generated .py file
python_template = '''%s
import sys
if __name__ == "__main__":
    try:
        ret = %s(%s)
        expected = %s
        if ret == expected:
            print("Test case passed.")
            sys.exit(0)
        else:
            print("%%s" %% ret)
            sys.exit(1)
    except Exception as e:
        import inspect
        frame = inspect.trace()[-1]
        print("Line %%d: %%s: %%s" %% (frame[2], type(e).__name__, e))
        sys.exit(1)
'''


def run_test_case(test_input, expected_output):
    p = subprocess.Popen(["python", test_fn, str(test_input), str(expected_output)], stdout=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    return rc, output

def match_test_cases(test_cases, code):
    failed_cases = []
    start = time.time()
    for case, res in test_cases.items():
        rc, output = run_test_case(case, res)
        if rc != 0:
            failed_cases.append((case, output))
    end = time.time()
    return failed_cases, (end - start) * 1000


def output_performance(test_cases, code):
    failed_cases, runtime = match_test_cases(test_cases, code)

    if not failed_cases:
        res = 'All test cases passed!\nRuntime: %dms.' % runtime
        return True, runtime, res

    first_fail = failed_cases[0]
    res = 'Test case failed.\nInput: %s\n%s' % (first_fail[0], first_fail[1])
    return False, 0, res


class CodeEvaluatorServicer(code_eval.CodeEvaluatorServicer):
    def Eval(self, request, context):
        write_to_file(test_fn, request.code) 
        success, time, res = output_performance(test_cases, request.code)
        return code_eval.EvalReply(response=res, success=success, time_taken=time)


def debug_print(string):
    print(string)


def make_sig(call_types, ret_types):
    call_sig = ""
    ret_sig = ""
    sys_arg_ind = 1

    call_fmt = "%s(sys.argv[%d])"
    for t in call_types:
        call_sig += call_fmt % (t.__name__, sys_arg_ind)
        sys_arg_ind += 1

    ret_fmt = "%s(sys.argv[%d])"
    for t in ret_types:
        ret_sig += call_fmt % (t.__name__, sys_arg_ind)
        sys_arg_ind += 1

    return call_sig, ret_sig

def write_to_file(filename, code):
    call_sig, ret_sig = make_sig(prog_call_sig, prog_ret_sig)
    content = python_template % (code, prog_name, call_sig, ret_sig)
    debug_print("Writing to file: %s:\n%s" % (filename, content))
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

    # Loop indefinitely, to keep application alive
    try:
        while True:
            # Sleep; nothing else to do
            time.sleep(3600)
    except KeyboardInterrupt:
        # Stop server if user does Ctrl+C
        server.stop(0)


# Run program if run as main
if __name__ == "__main__":
    serve()
