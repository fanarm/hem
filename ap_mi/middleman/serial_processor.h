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

   
 * SerialProcessor is a class template allowing user to choose the different serial class
 * to use in low layer for communication. It will handle the packet assembly and verification 
 * before handing the raw content to upper layer.
 * 
 * User should call serReceive() in the loop() function to receive UART data.
 * Once a packet is well received, the return value changes to PACKET_READY. 
 * User then should use serGetContent to retrieve the received packet.
 * 
 * Note: serGetContent only returns RxBuf address, not doing any data copy.
 *       User need ensure not to call serReceive() before RxBuf data has been consumed.
 * 
 */

#ifndef SERIAL_PROCESSOR_H
#define SERIAL_PROCESSOR_H


#define SERPROC_RX_PACKET_CONTINUE   0
#define SERPROC_RX_PACKET_READY      1
#define SERPROC_RX_PACKET_ERROR      2
#define SERPROC_RX_PACKET_READ_SUC   0
#define SERPROC_RX_PACKET_READ_FAIL  1

template<class S, uint8_t bufLen>
class SerialProcessor {
        S *serPort;
        uint8_t rxBuf[bufLen];
        uint8_t rxBufLoc;
        bool inPacket;
        bool packetReady;
        uint8_t pktLen;
        uint8_t pktHeader;
public:
        SerialProcessor(S *port, uint8_t header, uint8_t len):serPort(port),inPacket(false),pktHeader(header),pktLen(len){}
        ~SerialProcessor() {}
        void serBegin(long baudRate);
        uint8_t serReceive();
        uint8_t serGetContent(uint8_t **data);
        uint8_t serSendContent(uint8_t *data, uint8_t len);
        virtual bool packetCheck(uint8_t *buf) {return true;}
};

template<class S, uint8_t bufLen>
void SerialProcessor<S,bufLen>::serBegin(long baudRate) {
  serPort->begin(baudRate);
}

template<class S, uint8_t bufLen>
uint8_t SerialProcessor<S,bufLen>::serReceive() {
  uint8_t ret = SERPROC_RX_PACKET_CONTINUE;
  uint8_t i;
  if (packetReady) {
    ret = SERPROC_RX_PACKET_READY;
  } else {
    while (serPort->available()) {
      if (inPacket) {
        rxBuf[rxBufLoc] = serPort->read();
        if (++rxBufLoc == pktLen) { 
          rxBufLoc = 0;
          if (packetCheck(rxBuf)) {
            packetReady = true;
            inPacket = false;
            ret = SERPROC_RX_PACKET_READY;
            break;
          } else {
            inPacket = false;
            ret = SERPROC_RX_PACKET_ERROR;
            break;
          }
        }
      } else {
        if (serPort->read()==pktHeader) {
          rxBuf[0] = pktHeader;
          rxBufLoc = 1;
          inPacket = true;
        } else {
          // Wrong header received. Just continue.
        }
      }
    }
  }
  return ret;
}

template<class S, uint8_t bufLen>
uint8_t SerialProcessor<S,bufLen>::serGetContent(uint8_t **data) {
  uint8_t i;
  if (packetReady) {
    *data = rxBuf;
    packetReady = false;
    return SERPROC_RX_PACKET_READ_SUC;
  } else {
    return SERPROC_RX_PACKET_READ_FAIL;
  }
}

template<class S, uint8_t bufLen>
uint8_t SerialProcessor<S,bufLen>::serSendContent(uint8_t *data, uint8_t len) {
  uint8_t i;
  for(i=0;i<len;i++) serPort->write(data[i]);
  return 0;
}

#endif
