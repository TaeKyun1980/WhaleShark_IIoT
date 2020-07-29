 /*
 * File      : appwatchdog.c
*/
/*
 * @addtogroup STM32
 */
/*
  @{
*/

#include <rtthread.h>
#include <drivers/watchdog.h>
#ifdef RT_USING_FINSH
    #include <finsh.h>
#endif

#if defined (RT_USING_WDT)
#include "appwatchdog.h"
#include "debug.h"

#define MAX_WATCHDOG_TIME            20

#if (DEBUG_ENABLED & DEBUG_WDG)
    #define wdg_debug(fmt, ...);     {rt_kprintf("[WDG] "); rt_kprintf(fmt, ##__VA_ARGS__);}
#else
    #define wdg_debug(fmt, ...);
#endif

static void rt_wdg_thread_entry(void* parameter)
{
    rt_device_t dev;
    rt_err_t err;
    rt_uint32_t wdg_timeout = MAX_WATCHDOG_TIME;

    dev = rt_device_find("wdt");
    RT_ASSERT(dev != RT_NULL);
    dev->init(dev);
    
    err = rt_device_open(dev, RT_DEVICE_OFLAG_RDWR);
    RT_ASSERT(err == RT_EOK);

    err = rt_device_control(dev, RT_DEVICE_CTRL_WDT_SET_TIMEOUT, &wdg_timeout);
    RT_ASSERT(err == RT_EOK);

    err = rt_device_control(dev, RT_DEVICE_CTRL_WDT_START, RT_NULL);
    RT_ASSERT(err == RT_EOK); 

    while (1) 
    {
        wdg_debug("watchdog keep alive..!\r\n");
        rt_device_control(dev, RT_DEVICE_CTRL_WDT_KEEPALIVE, RT_NULL);       
        rt_thread_delay(7000);
    }
}

rt_err_t wdg_init()
{
    if (rt_thread_find("wdtask") != RT_NULL)
    {
        wdg_debug("watchdog already running..!\r\n");
        return -RT_EBUSY;
    }

	return RT_EOK;
}

void wdg_reflash(int argc, char **argv)
{
    rt_device_t dev;

    dev = rt_device_find("wdt");
    RT_ASSERT(dev != RT_NULL);

    rt_device_control(dev, RT_DEVICE_CTRL_WDT_KEEPALIVE, RT_NULL);

    return;
}
MSH_CMD_EXPORT(wdg_reflash, watchdog reflush)

#endif // RT_USING_WDT
/*@}*/
