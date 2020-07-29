/*
 * plccomm.h
 *
 */

#ifndef __DUSTCOMM_H__
#define __DUSTCOMM_H__

#define PK_TYPE_REQ				0x52 /* Request */
#define PK_TYPE_CFM				0x43 /* Confirm */
#define PK_TYPE_IND				0x69 /* Indicate */
#define PK_TYPE_RESP			0x72 /* Response */

#define PK_OPCODE_KEEPALIVE		0x00
#define PK_OPCODE_RESERVED		0x01
#define PK_OPCODE_ALLDATA		0xFF
#define PK_OPCODE_WARNING		(PK_OPCODE_RESERVED)

typedef struct pl_data_tag {
	rt_uint8_t type;
	rt_uint8_t opCode;
	rt_uint8_t size; // data size
	rt_uint8_t data[128];
}PlData;

typedef struct pl_data_Info_tag {
	PlData data;
	rt_uint8_t valid;
} PlDataInfo;

void PlcCommSendMessage(MqData_t *pMqData);
rt_bool_t InitPlcComm(void);

#endif /* __DUSTCOMM_H__ */
