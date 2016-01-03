#ifndef MM_H
#define MM_H

struct MM_DATA_STRUCT {
  byte mode;
  uint16_t fixed_output;
  bool vcc_en;
  uint16_t scale_thres[10];
  byte scale[10];
  uint16_t raw_pm;
  uint16_t vref;
};

#endif

