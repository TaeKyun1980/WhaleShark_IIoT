/*
 * File      : application.c.
*/

#include <board.h>
#include <drivers/rtc.h>
#ifdef RT_USING_FINSH
    #include <finsh.h>
#endif

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

#if defined (RT_USING_FINSH)
    void bk_read(int argc, char **argv)
    {
        rt_device_t rtc_dev;
        rt_err_t    err;
        rt_uint32_t idx;
        rt_bk_data_t bk_read;

        if (argc != 2) {
            rt_kprintf("usage : bk_read 3\r\n");
            rt_kprintf("read backup 3rd memory and return 4 bytes data\r\n");
            rt_kprintf("index [1 .. 19]\r\n");
            return;
        }

        rtc_dev = rt_device_find("rtc");
        if (rtc_dev == RT_NULL)
        {
            rt_kprintf("rtc is not installed\r\n");
            return;
        }

        idx = atoi(argv[1]);
        bk_read.bk_id = idx;

        err = rt_device_control(rtc_dev, RT_DEVICE_CTRL_RTC_GET_BKDATA, (void *)&bk_read);
        if (err != RT_EOK)
        {
            rt_kprintf("read backup memory error : %d\r\n", err);
            return;
        }
        rt_kprintf("backup memory %d => 0x%08x\r\n", idx, bk_read.bk_data);

        return;
    }
    MSH_CMD_EXPORT(bk_read, read backup memory);

    void bk_write(int argc, char **argv)
    {
        rt_device_t rtc_dev;
        rt_err_t    err;
        rt_uint32_t idx, value;
        rt_bk_data_t bk_read;

        if (argc != 3) {
            rt_kprintf("usage : bk_write 3 a5a57878\r\n");
            rt_kprintf("write backup 3rd memory writing value is 0xA5A57878\r\n");
            rt_kprintf("index [1 .. 19]\r\n");
            return;
        }

        rtc_dev = rt_device_find("rtc");
        if (rtc_dev == RT_NULL)
        {
            rt_kprintf("rtc is not installed\r\n");
            return;
        }

        idx = atoi(argv[1]);
        value = strtoul(argv[2], RT_NULL, 16);
        bk_read.bk_id = idx;
        bk_read.bk_data = value;

        err = rt_device_control(rtc_dev, RT_DEVICE_CTRL_RTC_SET_BKDATA, (void *)&bk_read);
        if (err != RT_EOK)
        {
            rt_kprintf("write backup memory error : %d\r\n", err);
            return;
        }
        rt_kprintf("write backup memory %d => 0x%08x\r\n", idx, (rt_uint32_t)bk_read.bk_data);

        bk_read.bk_data = 0;
        err = rt_device_control(rtc_dev, RT_DEVICE_CTRL_RTC_GET_BKDATA, (void *)&bk_read);
        if (err != RT_EOK)
        {
            rt_kprintf("read backup memory error : %d\r\n", err);
            return;
        }
        rt_kprintf("read BK memory %d => 0x%08x\r\n", idx, (rt_uint32_t)bk_read.bk_data);

        return;
    }
    MSH_CMD_EXPORT(bk_write, write backup memory);
#endif
