# IMU data transformer
Protect your serial port from code breaks! :sunglasses:
My code allows almost uninterrupted work with sensors connected to the serial port.
Data is read from the port, sent to Redis with virtually no delay, and then can be read by multiple Redis Workers without packet loss.
They can then be modified and sent through another Redis channel.
The rest of the instrumental was written exclusively for IMU.

Now let's describe in more detail what is there

# Table of Contents

1. [Code classes description](#Code-classes-description)
    1.1. [RedisPostman](#RedisPostman)
    1.2. [Madgwick](#Madgwick)
    1.3. [Accelerometer Calibration](#AccelerometerCalibration)
2. [How to use](#Use-cases)
    2.1. [Read data](#read-Data)
    2.2. [Calibrate](#calibration)
    2.2. [visualize](#visualization)
    2.3. [Modify Data](#Modify-Data)
<!-- 3. [Requirements](#requirements) -->

# Code classes description
## RedisPostman:

### RedisWorker
Class which read streams from the redis database.
```
# for async
worker = AsyncRedisWorker()

async for message in worker.subscribe(block=1, count=100000, dataClass=dataClass, channel=channel):
    print(message)
    # do smth with data
    ...

    # post new data
    await worker.broker.publish(channel=out_channel_name, message=json.dumps(message.to_dict()))

```
```
# for Sync
worker = RedisWorker()

for message in worker.subscribe(block=1, count=100000, dataClass=dataClass, channel=channel):
    print(message)
    # do smth with data
    ...

    # post new data
    worker.broker.publish(channel=out_channel_name, message=json.dumps(message.to_dict()))
```
dataClass - any class, described in models.py, which is inherited from Message class.


### MessageBroker
The one, who really publish and subscribes to the data from redis.
___
## Madgwick

### MadgwickFilter
The one who is responsible for non reliable results in quaternion visualization.
### Madgwick Plotter
Works with ***matplotlib***

___
## Accelerometer Calibration
### Calibration
The class describes workflow of Acceleration calibration.
It already knows everything, just call *update(xyz)*

___
# Use Cases:

## Read data:
    ### Start redis db:
    ```shell
    sudo systemctl start redis
    sudo python IMU_read_serial_to_redis_async.py
    ``` 


## Calibration:
    ```shell
    sudo python calibration_accel.py
    ```

    All data will be saved in file with name, saved in ***config.py*** as ***calib_data_filename***.

## Visualization:
    ```shell
    python visualise.py
    ```

    Choose the option you need. Be aware: You have to start processes which modify the raw data to e.g. plot calibrated data.

## Modify Data:
    To apply calibration to raw data, use:

    ```shell
    sudo python recalculate_data.py
    ```

    To transform data from euler to quaternions, use the script, which will post data into new stream. You still can access raw values.
    ```shell
    sudo python madgwick_transformer.py 
    ```



