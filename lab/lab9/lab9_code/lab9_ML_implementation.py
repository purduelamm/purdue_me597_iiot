import time
import board
import busio
import adafruit_adxl34x
from micropython import const
import datetime
import numpy as np
from scipy import stats, fft
import tensorflow as tf
import keras

i2c = busio.I2C(board.SCL, board.SDA)

acc = adafruit_adxl34x.ADXL345(i2c)

acc.data_rate = const(0b1111)

ratedict = {
    15: 3200, 14: 1600, 13: 800, 12: 400,
    11: 200, 10: 100, 9: 50, 8: 25,
    7: 12.5, 6: 6.25, 5: 3.13, 4: 1.56,
    3: 0.78, 2: 0.39, 1: 0.2, 0: 0.1
}

print("Output data rate is {} Hz".format(ratedict[acc.data_rate]))

def measureData(sensor: object, N: int):
    data_x, data_y, data_z = [], [], []
    for i in range(N):
        x_acc, y_acc, z_acc = sensor.acceleration
        data_x.append(x_acc)
        data_y.append(y_acc)
        data_z.append(z_acc)
    x_data = np.array(data_x)
    y_data = np.array(data_y)
    z_data = np.array(data_z)
    return x_data, y_data, z_data

def timeFeatures(data):
    mean = np.mean(data)
    std = np.std(data)
    rms = np.sqrt(np.mean(data ** 2))
    peak = np.max(abs(data))
    skew = stats.skew(data)
    kurt = stats.kurtosis(data)
    cf = peak / rms
    feature = np.array([mean, std, rms, peak, skew, kurt, cf], dtype=float)
    return feature

def freqFeatures(data):
    N = len(data)
    yf = 2 / N * np.abs(fft.fft(data)[:N // 2])
    yf[0] = 0
    feature = np.array(yf, dtype=float)
    return feature

def tensorNormalization(data, min_val, max_val):
    data_normal = (data - min_val) / (max_val - min_val)
    tensor = tf.cast(data_normal, tf.float32)
    tensor_feature = tf.reshape(tensor, [1, len(tensor)])
    return tensor_feature

def predict(model, data, threshold):
    reconstruction = model(data)
    if isinstance(reconstruction, dict):
        reconstruction = list(reconstruction.values())[0]
    loss = tf.keras.losses.mae(reconstruction, data).numpy()
    result = tf.math.less(loss, threshold).numpy()
    return result[0], loss[0]

## ============== MAIN ==============

if __name__ == "__main__":
    model_path = "/home/pi/lab9/models"
    model = keras.layers.TFSMLayer(model_path, call_endpoint="serving_default")

    # threshold = 0.021189
    # min_val = 0
    # max_val = 2.46385

    while True:
        try:
            x, y, z = measureData(acc, 1000)
            input_feature = freqFeatures(x)
            input_feature_normalized = tensorNormalization(input_feature, min_val, max_val)
            result = predict(model, input_feature_normalized, threshold)
            now = datetime.datetime.now()
            print("{0}: Model result={1}, MAE loss={2:.4f}".format(now, result[0], result[1]))
            time.sleep(1)

        except KeyboardInterrupt:
            raise
