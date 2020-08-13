/*
 * File      : application.c.
*/

#include <board.h>
#include <drivers/rtc.h>

#include "application.h"
#include <config/appconfig.h>
#include <device/uart/plccomm.h>
#include <network/networkmanager.h>

typedef struct _APPINFO
{
	rt_mq_t appMq;
	MqData_t mqData;
}AppInfo;

static AppInfo appInfo;

void ApplicationSendMessage(MqData_t *pMqData)
{
	if(-RT_EFULL == rt_mq_send(appInfo.appMq, (void *)&pMqData, sizeof(void*)))
	{
		rt_kprintf("Application Queue full - throw away\r\n");
	}
}

void DeviceReboot(void)
{
	rt_kprintf("Device Reboot After 2 seconds\r\n");
	rt_thread_delay(2000);
	NVIC_SystemReset();
}

rt_bool_t StartApplication(void)
{
	return StartNetworkManager();
}

static void app_main_thread(void *params)
{
	AppInfo *p_handle = (AppInfo *)params;
	MqData_t *pMqData = RT_NULL;

	while(1)
	{
		if(rt_mq_recv(p_handle->appMq, &pMqData, sizeof(void *), RT_WAITING_FOREVER) == RT_EOK)
		{
			MqData_t mqData;

			rt_memcpy(&mqData, pMqData, sizeof(mqData));
			switch(mqData.messge)
			{
			case SMSG_INC_DATA:
				break;
			}
		}
	}
}

void InitApplicationInfo(void)
{
	appInfo.appMq = RT_NULL;
}

rt_bool_t InitApplication(void)
{
    AppInfo *h_data = &appInfo;
	rt_bool_t retVal = RT_FALSE;
	rt_thread_t tid;

	InitApplicationInfo();

	h_data->appMq = rt_mq_create("app_mq", sizeof(MqData_t), APPLICATION_MQ_SIZE, RT_IPC_FLAG_FIFO);
	RT_ASSERT(RT_NULL != h_data->appMq);

    tid = rt_thread_create("application", app_main_thread, (void *)h_data, APPLICATION_STACK_SIZE, RT_MAIN_THREAD_PRIORITY, 20);
    RT_ASSERT(RT_NULL != tid);

	/* thread start  */
	rt_err_t err = rt_thread_startup(tid);
	RT_ASSERT(RT_EOK == err);

	if(RT_FALSE == (retVal=InitPlcComm()) || RT_FALSE == (retVal=InitNetworkManager()))
	{
		rt_kprintf("Init Applicaiotn failed.\r\n");
	}

	return retVal;
}
