import time

test_cases = {
    1: 1,
    2: 1,
    3: 2,
    4: 3,
    5: 5,
    6: 8
}

s = """
def fib(n):
    if n < 1:
        return None
    fib_matrix = [None] * (n + 1)
    fib_matrix[0] = 1
    fib_matrix[1] = 1
    for i in range(2, n):
        fib_matrix[i] = fib_matrix[i - 1] + fib_matrix[i - 2];
    return fib_matrix[n - 1]
"""
exec s

def match_test_cases(test_cases):
    failed_cases = []
    start = time.time()
    for case, res in test_cases.items():
        user_res = fib(case)
        if user_res != res:
            failed_cases.append((case, res, user_res))
    end = time.time()
    return failed_cases, (end - start) * 1000

def output_performance(test_cases):
    failed_cases, runtime = match_test_cases(test_cases)
    if not failed_cases:
        print 'All cases passed! Runtime: ', runtime, 'ms'
        return
    first_failed_case = failed_cases[0]
    print 'Test case failed. Input:', first_failed_case[0]
    print 'Expected :', first_failed_case[1], 'but got', first_failed_case[2], 'instead'

output_performance(test_cases)
