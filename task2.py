import multiprocessing
import concurrent.futures
import time

print('CPU core count:', multiprocessing.cpu_count(), '\n')

def factorize_single(*numbers):
    results = []
    for num in numbers:
        factors = [i for i in range(1, num + 1) if num % i == 0]
        results.append(factors)
    return tuple(results)


def factorize_multi(*numbers):
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(factorize_single, numbers))
    return tuple(results)


if __name__ == "__main__":
    print("Results Single:")
    start = time.perf_counter()
    a, b, c, d = factorize_single(1280, 2550, 999990, 106510600)
    print(a)
    print(b)
    print(c)
    print(d)
    finish = time.perf_counter()
    print(f'Finished in: {round(finish - start, 2)}', '\n')

    print("Results Multi:")
    start = time.perf_counter()
    a, b, c, d = factorize_multi(1280, 2550, 999990, 106510600)
    print(a)
    print(b)
    print(c)
    print(d)
    finish = time.perf_counter()
    print(f'Finished in: {round(finish - start, 2)}')
