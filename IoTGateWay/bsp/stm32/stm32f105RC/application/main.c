/*
 * File      : main.c
 * COPYRIGHT (C) 2020 
 */

/**
 * @addtogroup STM32
 */
/*@{*/

#include <rtthread.h>

#include "application.h"
#include "manufacture.h"
#include <util/appwatchdog.h>
#include <util/debug.h>
#include <device/uart/usbconsole.h>
#include <config/configuration.h>
#include <config/appconfig.h>

int main(void)
{
	rt_kprintf("Run %s(%s)\r\n", MODEL_NAME, PRODUCT_NAME);
	rt_err_t err = -RT_ERROR;

	if(RT_TRUE == InitUsbconsole() && RT_TRUE == InitConfiguration())
	{
		if(ENABLE == GetManufactureMode())
		{
			if(RT_TRUE == InitManufacture())
			{
				StartManufacture();
			}
		}
		else if(RT_TRUE == InitApplication())
		{
			StartApplication();
		}
	}

	return err;
}


/*@}*/
