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
 */

#ifndef SIMS_H
#define SIMS_H

#define COMMAND_HEADER                          0x65
#define COMMAND_LEN                             0x5

#define COMMAND_RW_BIT_MASK                     0x80
#define COMMAND_RW_READ                         0x00
#define COMMAND_RW_WRITE                        0x80

#define COMMAND_NAME_CLASS_MASK                 0x60
#define COMMAND_NAME_COMMON_CLASS               0x0
#define COMMAND_NAME_RESPONSE_CURVE_CLASS       0x20
#define COMMAND_NAME_STATUS_CLASS               0x60

#define COMMAND_NAME_INTPRT_MODE                0x01
#define COMMAND_NAME_FIXED_PM_OUTPUT_VAL        0x10
#define COMMAND_NAME_FIXED_VREF_OUTPUT_VAL      0x11
#define COMMAND_NAME_VCC_PM_EN                  0x15

#define COMMAND_NAME_RESPONSE_CURVE_MASK        0x30
#define COMMAND_NAME_RESPONSE_CURVE_THRES_BASE  0x20
#define COMMAND_NAME_RESPONSE_CURVE_THRES_END   0x2F
#define COMMAND_NAME_RESPONSE_CURVE_VAL_BASE    0x30
#define COMMAND_NAME_RESPONSE_CURVE_VAL_END     0x3F

#define COMMAND_NAME_LATEST_RAW_PM              0x60
#define COMMAND_NAME_SAMPLE_COUNT_FOR_AVERAGE_PM   0x61
#define COMMAND_NAME_AVERAGE_RAW_PM             0x62
#define COMMAND_NAME_LATEST_RAW_VREF            0x70
#define COMMAND_NAME_SAMPLE_COUNT_FOR_AVERAGE_VREF   0x71
#define COMMAND_NAME_AVERAGE_RAW_VREF           0x72

#define COMMAND_VALUE_INTPRT_MODE_OFF           0x0
#define COMMAND_VALUE_INTPRT_MODE_PASS_THRU     0x1
#define COMMAND_VALUE_INTPRT_MODE_FIXED         0x2
#define COMMAND_VALUE_INTPRT_MODE_SCALE         0x3

#define RESPONSE_HEADER                         0xE5
#define RESPONSE_LEN                            0x5

#endif
