# IMU data transformer
Protect your serial port from code breaks! :sunglasses:
My code allows almost uninterrupted work with sensors connected to the serial port.
Data is read from the port, sent to Redis with virtually no delay, and then can be read by multiple Redis Workers without packet loss.
They can then be modified and sent through another Redis channel.
The rest of the instrumental was written exclusively for IMU.

Now let's describe in more detail what is there

# Table of Contents
[Read data](#read-Data)\
[Calibrate](#calibration)\
[Visualization](#visualization)\
[Modify Data](#Modify-Data)\
[Debugging and Logger](#Debugging-and-Logging)
___


<a name="read-Data"/>

## Read data
### Start redis db:    
```zsh
sudo systemctl start redis
```
### Read IMU data from Serial port
```bash
sudo python IMU_read_serial_to_redis_async.py
```
<a name="calibration"/>
## Calibrate
```bash
sudo python calibration_accel.py
```
    
All data will be saved in file with name, saved in ***config.py*** as ***calib_data_filename***.


<a name="visualization"/>

## Visualization
There is all possible configurations for IMU data visualization - includes methods for plotting 3D rotations and 2D IMU data (calibrated and raw data).
```bash
python visualize.py
```    

Choose the option you need. Be aware: You have to start processes which modify the raw data to e.g. plot calibrated data.

<a name="Modify-Data"/>

## Modify Data
To apply calibration to raw data, use:
```bash
sudo python recalculate_data.py
```   

To transform data from euler to quaternions, use the script, which will post data into a new stream. You still can access raw values.
```shell
sudo python madgwick_transformer.py 
```
<a name="Debugging-and-Logging"/>

## Debugging and Logging:
Clear the terminal and Start to read logs messages from processes via ***read_logs.py***
### How to use?
Logger connects to Redis and stores Exceptions from all processes, which sends the data to related channel (the name log_message_channel defined in in config.py)
Also, a Log message has its own structure, described in **models.py** - LogMessage.