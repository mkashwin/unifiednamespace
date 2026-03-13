import time
import sys
import os

sys.path.append(os.path.abspath('02_mqtt-cluster/src'))

from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_helper import SpBMessageGenerator, convert_dict_to_dataset

gen = SpBMessageGenerator()

def bench_init_template():
    metrics = [Payload.Metric(name=f"m{i}") for i in range(1000)]

    start = time.perf_counter()
    for _ in range(1000):
        payload = Payload()
        gen.init_template_metric(payload, "test", metrics=metrics, version="1.0")
    end = time.perf_counter()
    print(f"init_template_metric Time: {end - start:.5f}s")

def bench_dataset():
    dataset_dict = {
        "columns": [f"col_{i}" for i in range(1000)],
        "types": [1] * 1000,
    }
    start = time.perf_counter()
    for _ in range(1000):
        convert_dict_to_dataset(dataset_dict)
    end = time.perf_counter()
    print(f"convert_dict_to_dataset Time: {end - start:.5f}s")

if __name__ == "__main__":
    bench_init_template()
    bench_dataset()
