import timeit
import json
from uns_sparkplugb.uns_spb_helper import convert_dict_to_dataset
from uns_sparkplugb.uns_spb_enums import SPBDataSetDataTypes

def benchmark():
    # create a large dataset dictionary
    # we'll test the difference in dataset conversion time
    # focus on large number of columns and types since that's what we are optimizing
    large_dataset_dict = {
        "columns": [f"col_{i}" for i in range(10000)],
        "types": [SPBDataSetDataTypes.Int32 for _ in range(10000)],
        "num_of_columns": 10000,
        "rows": [
            {
                "elements": [{"value": i} for i in range(10000)]
            }
        ]
    }

    # Run the function
    # time it

    # We will test dataset conversion with multiple iterations
    iterations = 100
    total_time = timeit.timeit(
        lambda: convert_dict_to_dataset(large_dataset_dict),
        number=iterations
    )
    print(f"Total time for {iterations} iterations: {total_time:.4f} seconds")
    print(f"Average time per iteration: {total_time/iterations:.6f} seconds")

if __name__ == '__main__':
    benchmark()
