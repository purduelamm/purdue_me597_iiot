import numpy as np
import pandas as pd
import torch
from scipy import stats, fft

# Time-domain data
def timeFeatures(data):
    feature = []
    for i in range(len(data)):
        mean = np.mean(data[i])                  # mean
        std = np.std(data[i])                    # standard deviation
        rms = np.sqrt(np.mean(data[i] ** 2))     # root mean square
        peak = np.max(np.abs(data[i]))           # peak
        skew = stats.skew(data[i])               # skewness
        kurt = stats.kurtosis(data[i])           # kurtosis
        cf = peak / rms if rms != 0 else 0.0     # crest factor
        feature.append(np.array([mean, std, rms, peak, skew, kurt, cf], dtype=float))
    return np.array(feature)

# DFT magnitude data
def freqFeatures(data):
    feature = []
    for i in range(len(data)):
        N = len(data[i])
        yf = 2 / N * np.abs(fft.fft(data[i])[:N // 2])  # DFT magnitude
        yf[0] = 0
        feature.append(np.array(yf, dtype=float))
    return np.array(feature)

def tensorNormalization(data):
    data = np.asarray(data, dtype=np.float32)
    data_t = torch.tensor(data, dtype=torch.float32)

    min_val = torch.min(data_t)
    max_val = torch.max(data_t)

    data_normal = (data_t - min_val) / (max_val - min_val + 1e-8)

    minVal = min_val.item()
    maxVal = max_val.item()

    return data_normal, minVal, maxVal  # torch tensor, min, max

## data loading
# All files should be in the same directory (folder)
normal_data_file = ""      # normal condition filename: You must change this
abnormal_data_file = ""    # abnormal condition filename: You must change this

df_normal = pd.read_csv(normal_data_file)
df_abnormal = pd.read_csv(abnormal_data_file)

frames = [df_normal, df_abnormal]
df = pd.concat(frames, ignore_index=True)

## Data Transformation
# X-axis: 'Xacc array [m/s2]'
# Y-axis: 'Yacc array [m/s2]'
# Z-axis: 'Zacc array [m/s2]'
AXIS = 'Xacc array [m/s2]'   # Select one of the above axes

# Exploding the values contained in selected column and converting the string values into float values
df_new = pd.concat(
    [df['Condition'], df[AXIS].str.split(' ', expand=True).astype(float)],
    axis=1
)
ds = df_new.copy()

# Converting the classifier into binary values
ds.loc[df['Condition'] == 'Normal', 'Status'] = 1
ds.loc[df['Condition'] == 'Abnormal', 'Status'] = 0
ds.drop('Condition', axis=1, inplace=True)

data = ds.values

# Define raw data without signal processing
raw_data = data[:, :-1].astype(np.float32)

# Labels: the last column
labels = data[:, -1].astype(np.float32)

time_data = timeFeatures(raw_data)
freq_data = freqFeatures(raw_data)

## Data (feature) selection
# Choose one: raw_data, time_data, or freq_data
input_feature = raw_data

# Normalize once and print min/max
input_feature_normalized, min_feature, max_feature = tensorNormalization(input_feature)

print("The minimum is {} and the maximum is {}.".format(min_feature, max_feature))