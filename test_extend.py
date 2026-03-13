import sys
import os
import time

sys.path.append(os.path.abspath('02_mqtt-cluster/src'))
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_helper import SpBMessageGenerator

metrics = [Payload.Metric(name=f"m{i}") for i in range(1000)]
gen = SpBMessageGenerator()

def test_append():
    start = time.perf_counter()
    for _ in range(1000):
        payload = Payload()
        metric = payload.metrics.add()
        for m in metrics:
            metric.template_value.metrics.append(m)
    return time.perf_counter() - start

def test_extend():
    start = time.perf_counter()
    for _ in range(1000):
        payload = Payload()
        metric = payload.metrics.add()
        metric.template_value.metrics.extend(metrics)
    return time.perf_counter() - start

print(f"append: {test_append():.5f}s")
print(f"extend: {test_extend():.5f}s")
