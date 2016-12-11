import proto.code_eval_pb2 as code_eval
import grpc
import sys

address = "localhost"
port = 8000


def main():
  if len(sys.argv) < 1:
    print("Not enough arguments.")
    printUsage()
    sys.exit(1)

  f = open(sys.argv[1], 'r')
  code = f.read()

  channel = grpc.insecure_channel('%s:%d' % (address, port))
  stub = code_eval.CodeEvaluatorStub(channel)

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
  main()
