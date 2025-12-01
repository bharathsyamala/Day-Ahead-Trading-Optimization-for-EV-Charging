### Directory/File Accessing Libraries ###

from pathlib import Path
import glob
import os


### Data Science Libraries ###

import numpy as np
import pandas as pd



### Data Visualization Libraries ###

import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns




###################

CUR_DIR = Path(__file__).resolve()
ROOT_DIR = CUR_DIR.parent.parent
RAW_DATA_DIR = ROOT_DIR/'data'/'raw'
PROCESSED_DATA_DIR = ROOT_DIR/'data'/'processed'

'''
print(CUR_DIR)
print(ROOT_DIR)
print(RAW_DATA_DIR)
print(PROCESSED_DATA_DIR)
'''






