![issue badge](https://img.shields.io/github/issues/dataignitelab/WhaleShark_IIoT)
![forks badge](https://img.shields.io/github/forks/dataignitelab/WhaleShark_IIoT)
![starts badge](https://img.shields.io/github/stars/dataignitelab/WhaleShark_IIoT)
![license badge](https://img.shields.io/github/license/dataignitelab/WhaleShark_IIoT)

## Abount Project: Equipment Monitor system for Smart Factory or Smart Farm
WhaleShark IIoT, an open source monitoring system for smart factories, is a IIoT-based process monitoring system.
 - Target Object
   - Process equipment and objects connected to various sensors
   - The factory manager can monitor the status of the equipment in real time by checking the values of various sensors installed in the equipment.

## Documents
 - [Document Home] Coming soon...
 
## Download
 - [Last Release] (https://github.com/dataignitelab/WhaleShark_IIoT)
 
## Modules
### WhaleShart IIoT Project consists of 4 modules:
- Embedded System for Sensor Device: The sensor value connected to the facility is read and transmitted to the gateway through RS485.
- IIoT gateway : The measured sensor value is sent to the agent of the cloud server.
- Gatway agent : It converts Modbus-based data transmitted through the gateway into human-readable data.
- TSDB agent : Insert human-readable data to TSDB(ex: InfluxDB)

## Facebook
 - [WhaleShark IIoT Facebook Group] (https://www.facebook.com/groups/whalesharkIIoT)
 
## Slack
 - [WhaleShark IIoT Slack] (https://data-centricworkspace.slack.com/archives/C018GNT7SKF)

## Contributing to WhaleShark IIoT
 - **Pull requests** require **feature branches**
   
## How to run
## Prerequest:
1. You need python3.x on Factory side, Server side
2. Server side system needs Redis, RabbitMQ, InfluxDB
If you need visualization engine, we will recommend Grafana.

#### Factory side:
1. Wiring the controller and the embedded computer.
2. Check the COM Port, and run bellow command
- IIoT gateway : python3 instrument_monitor.py
#### Server side:
- Gateway Agent: python3 iiot_server.py
- TSDB Agent: python3 iiot_mqtt_agent.py

## License
Licensed under the Apache License, Version 2.0
<br>

## korea
- (https://github.com/prismdata/WhaleShark_IIoT/blob/master/Readme.kr.md)
