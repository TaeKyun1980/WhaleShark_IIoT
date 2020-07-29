/*
 * File      : appwatchdog.h
 */

/**
 * @addtogroup STM32
 */
/*@{*/

#ifndef __APPWATCHDOG_H__
#define __APPWATCHDOG_H__

#if defined (RT_USING_WDT)

/* watchdog api */
rt_err_t wdg_init(void);

#endif

#endif // __APPWATCHDOG_H__

/*@}*/
