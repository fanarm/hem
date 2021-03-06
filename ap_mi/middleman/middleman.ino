/*
  Copyright 2016, Xun Jiang

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
  
 
  
  Code for a gadget which sit in middle of dust sensor of an air purifier and purifier's digital logic board.
  
  The purpose of gadget is to modify the raw reading from dust sensor, with the assistant from a bluetooth serial 
  where the modification instructions come from, in order to make the purifier work better.

  Two serial ports used. Hardware serial is used for receiving dust sensor's data and sending modified data to purifier.
  Software serial on digital pin 8(RX) and 9(TX) are used for communicating with smart home host via bluetooth serial.
  
 The circuit for use with SoftwareSerial
 Running on Sparkfun Pro Micro.
 * RX for bluetooth is SW RX    (digital pin 8, PB4/PCINT4)
 * TX for bluetooth is SW TX    (digital pin 9, PB5)
 * RX for Dust sensor is HW RX  (digital pin 0, PD2)
 * TX for Purifier is HW TX     (digital pin 1, PD3)

 The circuit for use with AltSoftSerial
 * RX for bluetooth is SW RX    (digital pin 4, PD4/ICP1)
 * TX for bluetooth is SW TX    (digital pin 9, PB5/OC1A)
 * RX for Dust sensor is HW RX  (digital pin 0, PD2)
 * TX for Purifier is HW TX     (digital pin 1, PD3)

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
    bool alterPM25(uint16_t *raw_pm, uint16_t *raw_vref, uint8_t mode, uint16_t *data1, uint8_t *data2);
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
bool PM25OutputProcessor<S>::alterPM25(uint16_t *raw_pm, uint16_t *raw_vref, uint8_t mode, uint16_t *data1, uint8_t *data2) {
  uint8_t t, i, *buf, txBuf[7];
  uint16_t ret, pm25out;
  t = this->serGetContent(&buf);
  if (t==SERPROC_RX_PACKET_READ_SUC) {
    memcpy(txBuf,buf,7);
    *raw_pm = txBuf[1]*256 + txBuf[2];
    *raw_vref = txBuf[3]*256 + txBuf[4];
    if (mode == COMMAND_VALUE_INTPRT_MODE_SCALE) {
      while ((*raw_pm)>(*data1)) {
        data1++;
        data2++;
      }
      pm25out = (*raw_pm)*(*data2);
    } 
    if (mode == COMMAND_VALUE_INTPRT_MODE_FIXED) pm25out = *data1;
    if ((mode == COMMAND_VALUE_INTPRT_MODE_FIXED)||(mode == COMMAND_VALUE_INTPRT_MODE_SCALE)) {
      txBuf[1] = (uint8_t)(pm25out >> 8);
      txBuf[2] = (uint8_t)(pm25out & 0x00FF);
      txBuf[5] = txBuf[1]+txBuf[2]+txBuf[3]+txBuf[4];
    }
    this->serSendContent(txBuf,7);
    return true;
  } else {
    return false;
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

SIMSProcessor<AltSoftSerial> sims_uart(new AltSoftSerial(4,9));
//SIMSProcessor<SoftwareSerial> sims_uart(new SoftwareSerial(8,9));
PM25OutputProcessor<HardwareSerial> pm25_uart(&Serial1);

void setup() {
  mm_data.mode = COMMAND_VALUE_INTPRT_MODE_FIXED;
  mm_data.vcc_en = false;
  mm_data.fixed_output = 0x0010;
  sims_uart.serBegin(9600);
  pm25_uart.serBegin(2400);
  Serial.begin(115200); // USB Serial for debugging.
  Serial.print("middleman:setup()\n");
}

void loop() {
  if ( (!mm_data.vcc_en) && (mm_data.mode==COMMAND_VALUE_INTPRT_MODE_FIXED)) {
      Serial.print("middleman:sending fixed_output\n");
      pm25_uart.writeData(mm_data.fixed_output);
      //sims_uart.writeData(COMMAND_NAME_FIXED_PM_OUTPUT_VAL,mm_data.fixed_output);
      delay(1000);
  } else {
    if (pm25_uart.serReceive()==SERPROC_RX_PACKET_READY) {
      if (mm_data.mode==COMMAND_VALUE_INTPRT_MODE_FIXED) {
        Serial.print("middleman:sending fixed_output after receiving\n");
        pm25_uart.alterPM25(&mm_data.raw_pm, &mm_data.raw_vref, mm_data.mode, &mm_data.fixed_output, NULL);
      } else if (mm_data.mode==COMMAND_VALUE_INTPRT_MODE_SCALE) {
        Serial.print("middleman:sending scaled output after receiving\n");
        pm25_uart.alterPM25(&mm_data.raw_pm, &mm_data.raw_vref, mm_data.mode, mm_data.scale_thres, mm_data.scale);
      } else if (mm_data.mode==COMMAND_VALUE_INTPRT_MODE_PASS_THRU) {
        Serial.print("middleman:sending unchanged output after receiving\n");
        pm25_uart.alterPM25(&mm_data.raw_pm, &mm_data.raw_vref, mm_data.mode, NULL, NULL);
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
      switch (cmd&COMMAND_NAME_CLASS_MASK) {
        case COMMAND_NAME_COMMON_CLASS:
        case COMMAND_NAME_STATUS_CLASS:
          switch (cmd&(~COMMAND_RW_BIT_MASK)) {
            case COMMAND_NAME_INTPRT_MODE:
              if ((cmd&COMMAND_RW_BIT_MASK)==COMMAND_RW_WRITE) {
                mm_data.mode = (uint8_t)data;
              }
              sims_uart.writeData(cmd,(uint16_t)mm_data.mode);
              break;
            case COMMAND_NAME_FIXED_PM_OUTPUT_VAL:
              if ((cmd&COMMAND_RW_BIT_MASK)==COMMAND_RW_WRITE) {
                mm_data.fixed_output = data;
              }
              sims_uart.writeData(cmd,mm_data.fixed_output);
              break;
            case COMMAND_NAME_VCC_PM_EN:
              if ((cmd&COMMAND_RW_BIT_MASK)==COMMAND_RW_WRITE) {
                mm_data.vcc_en = (data==1);
              }
              sims_uart.writeData(cmd,mm_data.vcc_en?1:0);
              break;
            case COMMAND_NAME_LATEST_RAW_PM:
              sims_uart.writeData(cmd,mm_data.raw_pm);
              break;
            case COMMAND_NAME_LATEST_RAW_VREF:
              sims_uart.writeData(cmd,mm_data.raw_vref);
              break;
          }
          break;
        case COMMAND_NAME_RESPONSE_CURVE_CLASS:
          if ((cmd&COMMAND_NAME_RESPONSE_CURVE_MASK)==COMMAND_NAME_RESPONSE_CURVE_THRES_BASE) {
            uint8_t reg_addr = (cmd&(~COMMAND_RW_BIT_MASK))-COMMAND_NAME_RESPONSE_CURVE_THRES_BASE;
            if ((cmd&COMMAND_RW_BIT_MASK)==COMMAND_RW_WRITE) {
              mm_data.scale_thres[reg_addr] = data;
            }
            sims_uart.writeData(cmd,mm_data.scale_thres[reg_addr]);
          } else {
            uint8_t reg_addr = (cmd&(~COMMAND_RW_BIT_MASK))-COMMAND_NAME_RESPONSE_CURVE_VAL_BASE;
            if ((cmd&COMMAND_RW_BIT_MASK)==COMMAND_RW_WRITE) {
              mm_data.scale[reg_addr] = (uint8_t)data;
            }
            sims_uart.writeData(cmd,(uint16_t)mm_data.scale[reg_addr]);            
          }
          break;          
      }
    }
  }
}
