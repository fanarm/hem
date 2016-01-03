/*
  Code for a gadget which sit in middle of dust sensor of an air purifier and purifier's digital logic board.
  
  The purpose of gadget is to modify the raw reading from dust sensor, with the assistant from a bluetooth serial 
  where the modification instructions come from, in order to make the purifier work better.

  Two serial ports used. Hardware serial is used for receiving dust sensor's data and sending modified data to purifier.
  Software serial on digital pin 8(RX) and 9(TX) are used for communicating with smart home host via bluetooth serial.
  
 The circuit: 
 Running on Sparkfun Pro Micro.
 * RX for Dust sensor is digital pin 8 (PB4)
 * TX for Purifier is digital pin 9 (PB5)
 * RX for bluetooth is HW RX (digital pin 0, PD2)
 * TX for bluetooth is HW TX (digital pin 0, PD3)

 */

#include <EEPROM.h>
#include <AltSoftSerial.h>
#include <SoftwareSerial.h>
#include "sims_protocol.h"
#include "serial_processor.h"
#include "mm.h"

#define PM25_INVALID_VALUE  0xFFFF

MM_DATA_STRUCT mm_data ;

template<class S> 
class SIMSProcessor : public SerialProcessor<S, 8> {
    uint8_t txPacket[5];
  public:
    SIMSProcessor(S *port):SerialProcessor<S,8>(port, 0x65, 5){txPacket[0]=0xE5;}
    bool readData(uint8_t *cmd, uint16_t *data);
    void writeData(uint8_t cmd, uint16_t data);
    virtual bool packetCheck(uint8_t *buf);
};

template<class S>
bool SIMSProcessor<S>::readData(uint8_t *cmd, uint16_t *data) {
  uint8_t ret, *buf;
  ret = this->serGetContent(&buf);
  if (ret==SERPROC_RX_PACKET_READ_SUC) {
    *cmd = buf[1];
    *data = buf[3]*256 + buf[2];
    return true;
  } else {
    return false;
  }
}

template<class S>
void SIMSProcessor<S>::writeData(uint8_t res, uint16_t data) {
  uint8_t t, i;
  txPacket[1] = res;
  txPacket[2] = (uint8_t)(data & 0x00FF);
  txPacket[3] = (uint8_t)(data >> 8);
  txPacket[4] = txPacket[1]+txPacket[2]+txPacket[3];
  this->serSendContent(txPacket,5);
  return;
}

template<class S> 
bool SIMSProcessor<S>::packetCheck(uint8_t *buf) {
  uint8_t i,sum=0;
  for(i=1;i<4;i++) sum+=buf[i];
  return (sum==buf[4]);
}


template<class S> 
class PM25OutputProcessor : public SerialProcessor<S, 8> {
    uint8_t txPacket[7];// = {0xAA, 0x00, 0x00, 0x00, 0x3E, 0x3E, 0xFF};
  public:
    PM25OutputProcessor(S *port):SerialProcessor<S,8>(port, 0xAA, 7){txPacket[0]=0xAA;txPacket[3]=0;txPacket[4]=0x3E;txPacket[6]=0xFF;}
    bool readData(uint16_t *pm25, uint16_t *vref);
    uint16_t alterPM25(uint8_t mode, uint16_t *data1, uint8_t *data2);
    void writeData(uint16_t pm25);
    bool packetCheck(uint8_t *buf);
};

template<class S> 
bool PM25OutputProcessor<S>::readData(uint16_t *pm25, uint16_t *vref) {
  uint8_t ret, *buf;
  ret = this->serGetContent(&buf);
  if (ret==SERPROC_RX_PACKET_READ_SUC) {
    *pm25 = buf[1]*256 + buf[2];
    *vref = buf[3]*256 + buf[4];
    return true;
  } else {
    return false;
  }
}

template<class S> 
uint16_t PM25OutputProcessor<S>::alterPM25(uint8_t mode, uint16_t *data1, uint8_t *data2) {
  uint8_t t, i, *buf, txBuf[7];
  uint16_t ret, pm25raw, pm25out;
  t = this->serGetContent(&buf);
  if (t==SERPROC_RX_PACKET_READ_SUC) {
    memcpy(txBuf,buf,7);
    pm25raw = txBuf[1]*256 + txBuf[2];
    if (mode == COMMAND_VALUE_INTPRT_MODE_SCALE) {
      while (pm25raw>(*data1)) {
        data1++;
        data2++;
      }
      pm25out = pm25raw*(*data2);
    } 
    if (mode == COMMAND_VALUE_INTPRT_MODE_FIXED) pm25out = *data1;
    if ((mode == COMMAND_VALUE_INTPRT_MODE_FIXED)||(mode == COMMAND_VALUE_INTPRT_MODE_SCALE)) {
      txBuf[1] = (uint8_t)(pm25out >> 8);
      txBuf[2] = (uint8_t)(pm25out & 0x00FF);
      txBuf[5] = txBuf[1]+txBuf[2]+txBuf[3]+txBuf[4];
    }
    this->serSendContent(txBuf,7);
    return pm25raw;
  } else {
    return PM25_INVALID_VALUE;
  }
}

template<class S> 
void PM25OutputProcessor<S>::writeData(uint16_t pm25) {
  uint8_t t, i;
  txPacket[1] = (uint8_t)(pm25 >> 8);
  txPacket[2] = (uint8_t)(pm25 & 0x00FF);
  txPacket[5] = txPacket[1]+txPacket[2]+txPacket[3]+txPacket[4];
  this->serSendContent(txPacket,7);
  return;
}

template<class S> 
bool PM25OutputProcessor<S>::packetCheck(uint8_t *buf) {
  uint8_t i,sum=0;
  for(i=1;i<5;i++) sum+=buf[i];
  return (sum==buf[5]);
}

//SIMSProcessor<AltSoftSerial> sims_uart(new AltSoftSerial(8,9));
SIMSProcessor<SoftwareSerial> sims_uart(new SoftwareSerial(8,9));
PM25OutputProcessor<HardwareSerial> pm25_uart(&Serial1);

void setup() {
  mm_data.mode = COMMAND_VALUE_INTPRT_MODE_FIXED;
  mm_data.vcc_en = true;
  mm_data.fixed_output = 0x0010;
  sims_uart.serBegin(9600);
  pm25_uart.serBegin(2400);
  Serial.begin(115200); // USB Serial for debugging.
  Serial.print("middleman:setup()\n");
}

void loop() {
  if ( (!mm_data.vcc_en) && (mm_data.mode==COMMAND_VALUE_INTPRT_MODE_FIXED)) {
      pm25_uart.writeData(mm_data.fixed_output);
      delay(1000);
  } else {
    if (pm25_uart.serReceive()==SERPROC_RX_PACKET_READY) {
      if (mm_data.mode==COMMAND_VALUE_INTPRT_MODE_FIXED) {
        mm_data.raw_pm = pm25_uart.alterPM25(COMMAND_VALUE_INTPRT_MODE_FIXED, &mm_data.fixed_output, NULL);
      } else if (mm_data.mode==COMMAND_VALUE_INTPRT_MODE_SCALE) {
        mm_data.raw_pm = pm25_uart.alterPM25(COMMAND_VALUE_INTPRT_MODE_FIXED, mm_data.scale_thres, mm_data.scale);
      }
    }
  }

  if (sims_uart.serReceive()==SERPROC_RX_PACKET_READY) {
    uint8_t cmd;
    uint16_t data;
    Serial.print("middleman:sims_uart:packet_ready\n");
    if (sims_uart.readData(&cmd,&data)) {
      Serial.print("middleman:sims_uart: cmd/data:");
      Serial.print(cmd,HEX);
      Serial.print("/");
      Serial.print(data,HEX);
      Serial.print("\n");
      switch (cmd&(~COMMAND_RW_BIT_MASK)) {
        case COMMAND_NAME_INTPRT_MODE:
          if ((cmd&COMMAND_RW_BIT_MASK)==COMMAND_RW_WRITE) {
            mm_data.mode = (uint8_t)data;
          }
          sims_uart.writeData(cmd,mm_data.mode);
          break;
        case COMMAND_NAME_FIXED_PM_OUTPUT_VAL:
          if ((cmd&COMMAND_RW_BIT_MASK)==COMMAND_RW_WRITE) {
            mm_data.fixed_output = data;
          }
          sims_uart.writeData(cmd,mm_data.mode);
          break;
      }
    }
  }
}
