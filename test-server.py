import time
import code_eval_pb2
import grpc
import concurrent.futures as futures
import time
import random

# Our service's address
address = "[::]"
port = 8000

test_cases = {
    1: 1,
    2: 1,
    3: 2,
    4: 3,
    5: 5,
    6: 8
}

def match_test_cases(test_cases, code):
    exec(code)
    failed_cases = []
    start = time.time()
    for case, res in test_cases.items():
        user_res = fib(case)
        if user_res != res:
            failed_cases.append((case, res, user_res))
    end = time.time()
    return failed_cases, (end - start) * 1000


def output_performance(test_cases, code):
    failed_cases, runtime = match_test_cases(test_cases, code)
    if not failed_cases:
        return 'All test cases passed! Runtime: %dms.' % runtime
    first_failed_case = failed_cases[0]
    return 'Test case failed.\n\tInput: %s\n\tExpected: %s but got %s instead.' % (first_failed_case[0], first_failed_case[1], first_failed_case[2])


class CodeEvaluatorServicer(code_eval_pb2.CodeEvaluatorServicer):
  def Eval(self, request, context):
    print("Got code:\n%s" % request.code)
    res = output_performance(test_cases, request.code)
    return code_eval_pb2.EvalReply(response=res, success=True, time_taken=0)


# Serve the service on the address:port
def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
  code_eval_pb2.add_CodeEvaluatorServicer_to_server(CodeEvaluatorServicer(), server)

  # Bind to address:port
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


serve()
