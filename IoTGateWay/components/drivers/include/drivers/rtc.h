/*
 * Copyright (c) 2006-2018, RT-Thread Development Team
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Change Logs:
 * Date           Author       Notes
 * 2012-10-10     aozima       first version.
 */

#ifndef __RTC_H__
#define __RTC_H__

#define RTC_BK_BANK1        1
#define RTC_BK_BANK2        2
#define RTC_BK_BANK3        3
#define RTC_BK_BANK4        4
#define RTC_BK_BANK5        5
#define RTC_BK_BANK6        6
#define RTC_BK_BANK7        7
#define RTC_BK_BANK8        8
#define RTC_BK_BANK9        9
#define RTC_BK_BANK10       10
#define RTC_BK_BANK11       11
#define RTC_BK_BANK12       12
#define RTC_BK_BANK13       13
#define RTC_BK_BANK14       14
#define RTC_BK_BANK15       15
#define RTC_BK_BANK16       16
#define RTC_BK_BANK17       17
#define RTC_BK_BANK18       18
#define RTC_BK_BANK19       19
#define RTC_BK_BANK20       20
#define RTC_BK_BANK21       21

struct rt_bk_data_tag
{
    rt_uint32_t bk_id;
    rt_uint32_t bk_data;
};
typedef struct rt_bk_data_tag rt_bk_data_t;

rt_err_t set_date(rt_uint32_t year, rt_uint32_t month, rt_uint32_t day);
rt_err_t set_time(rt_uint32_t hour, rt_uint32_t minute, rt_uint32_t second);

int rt_soft_rtc_init(void);
int rt_rtc_ntp_sync_init(void);

#endif /* __RTC_H__ */
