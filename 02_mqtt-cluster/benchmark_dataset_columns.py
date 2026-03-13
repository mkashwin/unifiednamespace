import time
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload

def benchmark_append(columns_list):
    dataset = Payload.DataSet()
    start_time = time.perf_counter()
    for col in columns_list:
        dataset.columns.append(col)
    end_time = time.perf_counter()
    return end_time - start_time

def benchmark_extend(columns_list):
    dataset = Payload.DataSet()
    start_time = time.perf_counter()
    dataset.columns.extend(columns_list)
    end_time = time.perf_counter()
    return end_time - start_time

if __name__ == "__main__":
    num_columns = 100000
    columns_list = [f"col_{i}" for i in range(num_columns)]

    # Warmup
    _ = benchmark_append(columns_list)
    _ = benchmark_extend(columns_list)

    num_iterations = 100
    append_time = 0
    extend_time = 0

    for _ in range(num_iterations):
        append_time += benchmark_append(columns_list)
        extend_time += benchmark_extend(columns_list)

    print(f"Number of columns: {num_columns}")
    print(f"Number of iterations: {num_iterations}")
    print(f"Total time (append): {append_time:.6f} seconds")
    print(f"Total time (extend): {extend_time:.6f} seconds")

    if extend_time < append_time:
        improvement = ((append_time - extend_time) / append_time) * 100
        print(f"Improvement: {improvement:.2f}% faster")
    else:
        print("Extend is slower!")
