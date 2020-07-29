/*
 * networkmanager.c
 *
 */
#include <rtthread.h>

#include <config/appconfig.h>
#include <network/wifi/wifi.h>

#include "networkmanager.h"

#define TCP_BUFFER_MAX	256

typedef struct _NetworkInfo
{
	rt_mq_t networkManagerMq;
	rt_thread_t tid;

	rt_uint8_t tcpSendBuffer[TCP_BUFFER_MAX];
}NetworkInfo;

NetworkInfo networkInfo;

void NetworkMangerSendMessage(MqData_t *pMqData)
{
	if(-RT_EFULL == rt_mq_send(networkInfo.networkManagerMq, (void *)&pMqData, sizeof(void*)))
	{
		rt_kprintf("NetworkManager Queue full - throw away\r\n");
	}
}

void SendData(rt_uint8_t *pData, rt_size_t dataSize)
{
	if( 0 < dataSize )
	{
		MqData_t data;
		data.messge = SMSG_TCP_SEND_DATA;
		data.size = dataSize;
		rt_memcpy(data.data,pData,dataSize);
		NetworkMangerSendMessage(&data);
	}
}

void NetworkManagerThread(void *params)
{
	NetworkInfo *p_handle = (NetworkInfo *)params;
	MqData_t *pMqData = RT_NULL;

	SendWifiCommand(CMD_QUERY_MODE);

	while(1)
{
		if(rt_mq_recv(p_handle->networkManagerMq, &pMqData, sizeof(void *), RT_WAITING_FOREVER) == RT_EOK)
		{
			NetworkInfoData networkInfoData;
			MqData_t mqData;
			rt_memcpy(&mqData, pMqData, sizeof(mqData));

			switch(mqData.messge)
			{
			case SMSG_WIFI_OK:
				rt_kprintf("Wi-Fi Response: OK\r\n");
				rt_memcpy(&networkInfoData, mqData.data, sizeof(networkInfoData));
				switch(networkInfoData.networkStatus)
				{
				case STATUS_GET_WIFI_MODE:
					switch(networkInfoData.data[0])
					{
					case StationMode:
						SendWifiCommand(CMD_QUERY_DHCP);
						break;
					case NullMode:
					case SoftApMode:
					case SoftAp_StationMode:
						SendWifiCommand(CMD_SET_MODE);
						break;
					}
					break;
				case STATUS_NONE:
				case STATUS_CONNECT_WIFI:
					rt_kprintf("AP Connection Success\r\n");
					SendWifiCommand(CMD_QUERY_AP_INFO);
					break;
				case STATUS_GET_DHCP_INFO:
					if( RT_TRUE == networkInfoData.data[DHCP_COMPARE_RESULT]) //Result
					{
						SendWifiCommand(CMD_CONNECT_AP);
					}
					else
					{
						SendWifiCommand(CMD_SET_DHCP); //Set DHCP
					}
					break;
				case STATUS_SET_DHCP:
					rt_kprintf("Set DHCP Success\r\n");
					SendWifiCommand(CMD_CONNECT_AP);
					break;
				case STATUS_GET_AP_INFO:
					if( RT_TRUE == networkInfoData.data[DHCP_MODE_INFO])
					{
						SendWifiCommand(CMD_TCP_CONNECT);//if dhcp enable
					}
					else
					{
					    SendWifiCommand(CMD_QUERY_LOCAL_INFO);//if dhcp disable
					}
					break;
				case STATUS_SET_LOCAL_INFO:
					SendWifiCommand(CMD_QUERY_LOCAL_INFO);//if dhcp disable
					break;
				case STATUS_GET_LOCAL_INFO:
					if( CHANGE_LOCAL_INFO != networkInfoData.data[LOCAL_IP_INDEX] && CHANGE_LOCAL_INFO != networkInfoData.data[GATEWAY_IP_INDEX] &&  CHANGE_LOCAL_INFO != networkInfoData.data[NETMASK_IP_INDEX])
					{
						SendWifiCommand(CMD_TCP_CONNECT); //TCP connect
					}
					else
					{
						SendWifiCommand(CMD_SET_LOCAL_INFO); // Set Local Information
					}
					break;
				case STATUS_TCP_CONNECT:
					rt_kprintf("TCP Connection Success\r\n");
					break;
				case STATUS_READY_TO_SEND_DATA:
					rt_kprintf("Send the Data. \r\n");
					TcpSendData(p_handle->tcpSendBuffer);
					break;
				case STATUS_SEND_DATA:
					rt_kprintf("Success Sending Data. \r\n");
					rt_memset(p_handle->tcpSendBuffer,'\0',TCP_BUFFER_MAX);
					break;
				default:
					break;
				}
				break;
			case SMSG_WIFI_ERROR:
				rt_kprintf("Wi-Fi Response: ERROR\r\n");
				rt_memcpy(&networkInfoData, mqData.data, sizeof(networkInfoData));
				switch(networkInfoData.networkStatus)
				{
				default:
					break;
				}
				break;
			case SMSG_WIFI_FAIL:
				rt_kprintf("Wi-Fi Response: FAIL\r\n");
				break;
			case SMSG_WIFI_TIMEOUT:
				rt_kprintf("Wi-Fi Response Timeout\r\n");
				rt_kprintf("Check Wi-Fi Module\r\n");
				break;
			case SMSG_TCP_SEND_DATA:
				rt_memcpy(&p_handle->tcpSendBuffer, mqData.data, mqData.size);
				TcpSetDataLength(mqData.size);
				break;
			default:
				break;
			}
		}
	}
}

rt_bool_t StartNetworkManager(void)
{
	return rt_thread_startup(networkInfo.tid);
}

void InitNetworkManagerInformation(void)
{
	networkInfo.networkManagerMq = RT_NULL;
	networkInfo.tid = RT_NULL;
}

void DeInitNetworkManager(void)
{

}

rt_bool_t InitNetworkManager(void)
{
	NetworkInfo *h_data = &networkInfo;
	rt_bool_t retVal = RT_FALSE;

	InitNetworkManagerInformation();

	h_data->networkManagerMq = rt_mq_create("networkManagerMq", sizeof(MqData_t), NETWORKMANAGER_MQ_SIZE, RT_IPC_FLAG_FIFO);
	RT_ASSERT(RT_NULL != h_data->networkManagerMq);

	h_data->tid = rt_thread_create("networkmanager", NetworkManagerThread, (void *)h_data, NETWORKMANAGER_STACK_SIZE, RT_MAIN_THREAD_PRIORITY, 20);
	RT_ASSERT(RT_NULL != h_data->tid);

	return (retVal=InitWifi());
}
