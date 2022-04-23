import json 
import pandas as pd 
import numpy as np

with open("input_data_3.txt") as json_file:
    data = json.load(json_file)
    
print(data)