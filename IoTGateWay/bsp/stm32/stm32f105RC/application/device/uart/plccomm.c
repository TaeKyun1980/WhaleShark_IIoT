/*
 * plccomm.c
 *
 */
#include <string.h>

#include <rtthread.h>
#ifdef RT_USING_FINSH
#	include <finsh.h>
#endif
#include <common/smsgdef.h>
#include <device/uart/plccomm.h>
#include "application.h"
#include <common/common.h>
#include <config/appconfig.h>

typedef struct dustCommInfo_tag {
	rt_mq_t plcMq;
	MqData_t mqData;

	rt_device_t uport;
	rt_event_t  rx_event;

	PlDataInfo plDataInfo;
	rt_uint8_t txBuf[RT_SERIAL_RB_BUFSZ];
	rt_uint8_t rxBuf[RT_SERIAL_RB_BUFSZ];
} PlcCommInfo;

static PlcCommInfo plcCommInfo;

void PlcCommSendMessage(MqData_t *pMqData)
{
	if(-RT_EFULL == rt_mq_send(plcCommInfo.plcMq, (void *)&pMqData, sizeof(void*)))
	{
		rt_kprintf("DustComm Queue full - throw away\r\n");
	}
}

static rt_err_t dustcomm_rx_ind(rt_device_t dev, rt_size_t size)
{
    return rt_event_send(plcCommInfo.rx_event, SMSG_RX_DATA);
}

static rt_size_t plccomm_tx_data(rt_uint8_t *data, rt_size_t tx_size)
{
	rt_int32_t remain = tx_size;
	rt_size_t written = 0;

	if(RT_NULL != data && 0 < tx_size)
	{
		do {
			if(0 < (written=rt_device_write(plcCommInfo.uport, 0, (data+written), remain)))
			{
				remain -= written;
			}
		} while(0 < remain);
	}

	return written;
}

static rt_size_t MakePayloadData(rt_uint8_t pkType, rt_uint8_t opCode, rt_uint8_t *plData, rt_uint16_t plSize)
{
	rt_kprintf("Make payload data. type:0x%02x, opcode:0x%02x, size:%u\r\n", pkType, opCode, plSize);
	rt_uint8_t *pos = plcCommInfo.txBuf;
	rt_uint8_t plBuf[128], *plPos=plBuf;
	rt_uint16_t u16Val;
	rt_size_t size = 0;

	*pos++ = STX;
	pos += sizeof(rt_uint16_t); // skip length field

	*plPos++ = pkType;
	*plPos++ = opCode;
	if(0 < plSize && RT_NULL != plData)
	{
		rt_memcpy(plPos, plData, plSize);
		plPos += plSize;
	}

	if(0 < (u16Val=base16_encode(plBuf, (rt_uint16_t)(plPos-plBuf), pos)))
	{
		rt_uint16_t len = u16Val;
		rt_uint8_t crc;

		pos = &plcCommInfo.txBuf[1]; // move length field

		u16Val = HTONS(u16Val);
		rt_memcpy(pos, &u16Val, sizeof(u16Val));
		pos += sizeof(u16Val);

		crc = chechsum_xor(pos, len);
		pos += len;

		*pos++ = crc;
		*pos++ = ETX;

		size = (pos-plcCommInfo.txBuf);
		BufferShow(plcCommInfo.txBuf, size);
	}
	else
	{
		rt_kprintf("Base16 encoding failed.\r\n");
	}

	return size;
}

static rt_size_t ParserReceiveData(rt_uint8_t *p_base, rt_size_t rx_size, PlDataInfo *plDataInfo)
{
	rt_size_t consumed = 0;

	if(RT_NULL != p_base && 0 < rx_size)
	{
		rt_uint8_t *begin=p_base, *end=begin, *last=(p_base+rx_size);

		do {
			if(ETX == *end)
			{
				do {
					if(STX == *begin)
					{
						rt_uint16_t u16Val, plLen;
						rt_uint8_t *plPos, u8Val=sizeof(u16Val), crc;
						PlData *plData = &plDataInfo->data;
						rt_uint8_t decBuf[128];

						begin++; /* skip STX */

						// Get Payload length
						rt_memcpy(&plLen, begin, u8Val);
						plLen = NTOHS(plLen);
						begin += u8Val;
						plPos = begin; // save payload position
						
						u8Val = chechsum_xor(begin, plLen);
						begin += plLen;
						crc = *begin;
						*begin = '\0'; // add null (must be)

						if(u8Val != crc)
						{ // check crc
							rt_kprintf("CRC Failed.\r\n");
						}
						else if(0 == (u16Val=base16_decode(plPos, plLen, decBuf)))
						{ // base16 decoding
							rt_kprintf("Base16 Decoding Failed.\r\n");
						}
						else
						{
							// decoding payload
							uint8_t *pl = decBuf;

							// pakect type
							plData->type = *pl++;
							// operation code
							plData->opCode = *pl++;
							if(0 < (plData->size=(u16Val-2)))
							{
								rt_memcpy(plData->data, pl, plData->size);
							}
							plDataInfo->valid = ENABLE;
						}
						
						begin = end;
					}
				} while(++begin < end);
			}
		} while(++end < last);

		consumed = (rt_size_t)(begin-p_base);
	}

	return consumed;
}

static void plccomm_rx_thread(void *params)
{
    PlcCommInfo *p_handle = (PlcCommInfo *)params;
	rt_uint8_t *pBuf = p_handle->rxBuf;	
	rt_size_t uRemain = 0;
	rt_uint32_t events;

    rt_err_t err = rt_device_open(p_handle->uport, RT_DEVICE_OFLAG_RDWR | RT_DEVICE_FLAG_INT_RX);
	RT_ASSERT(err == RT_EOK);

	rt_device_set_rx_indicate(p_handle->uport, dustcomm_rx_ind);
	while(1)
	{	
		if(RT_EOK == (err=rt_event_recv(p_handle->rx_event, SMSG_RX_DATA, (RT_EVENT_FLAG_OR|RT_EVENT_FLAG_CLEAR), RT_WAITING_FOREVER, &events))
			&& (SMSG_RX_DATA & events))
		{
			rt_size_t ulBytes;

			do {
				if(RT_SERIAL_RB_BUFSZ <= uRemain)
				{
					uRemain = 0;
				}

				if((ulBytes=rt_device_read(p_handle->uport, 0, (pBuf+uRemain), (RT_SERIAL_RB_BUFSZ-uRemain))) > 0)
				{
					rt_size_t consumed = ParserReceiveData(pBuf, (uRemain += ulBytes), &p_handle->plDataInfo);
					if(consumed > 0 && ((uRemain -= consumed) > 0))
					{
						memmove(pBuf, pBuf+consumed, uRemain);
					}
				}
			} while(0 < ulBytes);

			if(ENABLE == p_handle->plDataInfo.valid)
			{
				PlData *plData = &p_handle->plDataInfo.data;

				rt_kprintf("(DustComm)Receive PK(Type:0x%02x, OpCode:0x%02x)\r\n", plData->type, plData->opCode);
				if(PK_TYPE_REQ == plData->type)
				{
					if(PK_OPCODE_KEEPALIVE == plData->opCode)
					{
						rt_size_t size = MakePayloadData(PK_TYPE_CFM, PK_OPCODE_KEEPALIVE, RT_NULL, 0);

						if(0 < size)
						{
							plccomm_tx_data(p_handle->txBuf, size);
						}
					}
					else
					{
						p_handle->mqData.messge = SMSG_REQ_DATA;
						rt_memcpy(p_handle->mqData.data, plData, p_handle->mqData.size=sizeof(PlData));
						ApplicationSendMessage(&p_handle->mqData);
					}
				}
				else
				{
					switch(plData->type)
					{
					case PK_TYPE_CFM:
						rt_kprintf("PK type confirmed.\r\n"); break;
					case PK_TYPE_IND:
						rt_kprintf("PK type indicate.\r\n"); break;
					case PK_TYPE_RESP:
						rt_kprintf("PK type response.\r\n"); break;
					}
				}

				p_handle->plDataInfo.valid = DISABLE;
			}
		}
	}
}

static void plccomm_main_thread(void *params)
{
    PlcCommInfo *p_handle = (PlcCommInfo *)params;
	MqData_t *pMqData = RT_NULL;

	while(1)
	{	
		if(rt_mq_recv(p_handle->plcMq, &pMqData, sizeof(void *), RT_WAITING_FOREVER) == RT_EOK)
		{
			MqData_t mqData;
			rt_size_t size;			
			PlData plData;

			rt_memcpy(&mqData, pMqData, sizeof(MqData_t));
			switch(mqData.messge)
			{
			case SMSG_REQ_DATA:
				rt_kprintf("(PlcComm)Request data.\r\n");
				break;
			case SMSG_RESP_DATA:
			case SMSG_INC_DATA:
				rt_memcpy(&plData, mqData.data, mqData.size);
				if(SMSG_RESP_DATA == mqData.messge)
				{
				rt_kprintf("(PlcComm)Response data. PL(type:0x%02x, opcode:0x%02x)\r\n", plData.type, plData.opCode);
				}
				else
				{
					rt_kprintf("(PlcComm)Indicate data. PL(type:0x%02x, opcode:0x%02x)\r\n", plData.type, plData.opCode);
				}

				if(0 < (size=MakePayloadData(plData.type, plData.opCode, plData.data, plData.size)))
				{
					plccomm_tx_data(p_handle->txBuf, size);
				}
				break;
			}
		}
	}
}

void InitPlcCommInfo(void)
{
	plcCommInfo.plcMq = RT_NULL;

	plcCommInfo.uport = RT_NULL;
	plcCommInfo.rx_event = RT_NULL;

	rt_memset(&plcCommInfo.plDataInfo, 0, sizeof(plcCommInfo.plDataInfo));
}	

rt_bool_t InitPlcComm(void)
{
	rt_kprintf("Initialize PlcComm.\r\n");
    PlcCommInfo *h_data = &plcCommInfo;
    rt_thread_t tid_main, tid_rx;

    InitPlcCommInfo();

	h_data->plcMq = rt_mq_create("plc_mq", sizeof(MqData_t), PLCCOMM_MQ_SIZE, RT_IPC_FLAG_FIFO);
	RT_ASSERT(RT_NULL != h_data->plcMq);

    h_data->uport = rt_device_find(UART1_DEV_NAME);
    RT_ASSERT(h_data->uport != RT_NULL);	

    h_data->rx_event = rt_event_create("plccomm_rx", RT_IPC_FLAG_FIFO);
    RT_ASSERT(h_data->rx_event != RT_NULL);

    tid_main = rt_thread_create("plccomm_main_thread", plccomm_main_thread, (void *)h_data, PLCCOMMM_STACK_SIZE, RT_MAIN_THREAD_PRIORITY, 20);
    RT_ASSERT(tid_main != RT_NULL);

    tid_rx = rt_thread_create("plccomm_rx_thread", plccomm_rx_thread, (void *)h_data, PLCCOMMM_STACK_SIZE, RT_MAIN_THREAD_PRIORITY, 20);
    RT_ASSERT(tid_rx != RT_NULL);

    /* thread start  */
    return (RT_EOK == rt_thread_startup(tid_main) && RT_EOK == rt_thread_startup(tid_rx));
}
