#include "driver/mcpwm.h"
#define AVENUM 4
#define SWPIN 16
#define LEDPIN 15

volatile uint32_t aveInterval[4];
volatile uint16_t eventCount[4]={0, 0, 0, 0};

uint32_t initialInterval[4];

void setup() {
  pinMode(SWPIN, INPUT_PULLUP);
  pinMode(LEDPIN, OUTPUT);
  iCapSetup();
  Serial.begin(9600);
}

void loop() {
  if(digitalRead(SWPIN)==0){
    for(int i=0; i<4; i++){
      initialInterval[i] = aveInterval[i];
    }
  }

  Serial.print(initialInterval[0]);
  Serial.print(" ");
  Serial.print(aveInterval[0]);
  Serial.print(" ");
  Serial.print(aveInterval[1]);
  Serial.print(" ");
  Serial.print(aveInterval[2]);
  Serial.print(" ");
  Serial.println(aveInterval[3]);

  if(aveInterval[0] > initialInterval[0]*1.5){
    digitalWrite(LEDPIN, HIGH);
  }else{
    digitalWrite(LEDPIN, LOW);
  }
  delay(100);
}
