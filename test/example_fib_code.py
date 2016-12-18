def fib(n):
    if n < 1:
        return None
    fib_matrix = [None] * (n + 1)
    fib_matrix[0] = 1
    fib_matrix[1] = 1
    for i in range(2, n):
        fib_matrix[i] = fib_matrix[i - 1] + fib_matrix[i - 2]
    return fib_matrix[n - 1]
