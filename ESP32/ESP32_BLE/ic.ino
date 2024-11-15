bool iCapCallBack(mcpwm_unit_t mcpwm, mcpwm_capture_channel_id_t cap_channel, const cap_event_data_t *edata, void *user_data)
{
  static uint32_t timeStamp[4][AVENUM];
  static uint16_t index[4]={0,0,0,0};
  uint32_t oldestStamp, newStamp;
  int8_t inlineChannel; 

  inlineChannel = mcpwm*3 + cap_channel;
  oldestStamp = timeStamp[inlineChannel][index[inlineChannel]];
  newStamp = edata->cap_value;
  timeStamp[inlineChannel][index[inlineChannel]] = newStamp;
  aveInterval[inlineChannel] = (newStamp - oldestStamp) / AVENUM;
  index[inlineChannel] += 1;
  if(index[inlineChannel] == AVENUM) index[inlineChannel] =0;
  eventCount[inlineChannel] += 1;
  return false;
}
/*----------------------------------------------------------------------------------------------------------------------------*/
void iCapSetup(void)
{
  mcpwm_capture_config_t iCapCallSetup;
  iCapCallSetup.cap_edge = MCPWM_NEG_EDGE;
  iCapCallSetup.cap_prescale = 1;
  iCapCallSetup.user_data = NULL;
  
  iCapCallSetup.capture_cb = iCapCallBack;
  mcpwm_gpio_init(MCPWM_UNIT_0, MCPWM_CAP_0, 34);
  mcpwm_capture_enable_channel(MCPWM_UNIT_0, MCPWM_SELECT_CAP0, &iCapCallSetup );
  mcpwm_gpio_init(MCPWM_UNIT_0, MCPWM_CAP_1, 25);
  mcpwm_capture_enable_channel(MCPWM_UNIT_0, MCPWM_SELECT_CAP1, &iCapCallSetup );
  mcpwm_gpio_init(MCPWM_UNIT_0, MCPWM_CAP_2, 26);
  mcpwm_capture_enable_channel(MCPWM_UNIT_0, MCPWM_SELECT_CAP2, &iCapCallSetup );
  mcpwm_gpio_init(MCPWM_UNIT_1, MCPWM_CAP_0, 27);
  mcpwm_capture_enable_channel(MCPWM_UNIT_1, MCPWM_SELECT_CAP0, &iCapCallSetup );
}