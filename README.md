## Abount Project: Equipment Monitor system for Smart Factory or Smart Farm
WhaleShark IIoT, an open source monitoring system for smart factories, is a IIoT-based process monitoring system.
 - Target Object
   - Process equipment and objects connected to various sensors
   - The factory manager can monitor the status of the equipment in real time by checking the values of various sensors installed in the equipment.

## Documents
 - [Document Home] Will open in July
 
## Download
 - [Last Release] (https://github.com/dataignitelab/WhaleShark_IIoT)
 
## Modules
### WhaleShart IIoT Project consists of 4 modules:
- Embedded System for Sensor Device: The sensor value connected to the facility is read and transmitted to the gateway through RS485.
- IIoT gateway : The measured sensor value is sent to the agent of the cloud server.
- Gatway agent : It converts Modbus-based data transmitted through the gateway into human-readable data.
- TSDB agent : Insert human-readable data to TSDB(ex: InfluxDB)

## Facebook
 - [WhaleShark IIoT Facebook Group](Will open in July.)

## Contributing to WhaleShark IIoT
 - **Pull requests** require **feature branches**
   
## How to build and develop WhaleShart IIoT Project
- IIoT gateway : Will use RT-Thread as RT-OS(.https://github.com/RT-Thread/rt-thread)
- Gateway Agent : Will open in July
- TSDB Agent : Will open in August

## License
Licensed under the Apache License, Version 2.0
<br>

## korea
https://github.com/prismdata/WhaleShark_IIoT/blob/master/Readme.kr.md
