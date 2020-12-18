#define SIGNALPIN 3
#define INVERTPIN 4
#define INPUTPIN 12

int preservedstate;

void setup() {
  pinMode(SIGNALPIN, OUTPUT);
  pinMode(INVERTPIN, OUTPUT);
  pinMode(INPUTPIN, INPUT);
  preservedstate = LOW;
}

void loop() {
  int state = digitalRead(INPUTPIN);
  if(preservedstate != state){
    if(state == HIGH){
      digitalWrite(INVERTPIN, LOW);
    }
    if(state == LOW){
      digitalWrite(INVERTPIN, HIGH);
    }
    analogWrite(SIGNALPIN, 127);
    delay(3000);
    analogWrite(SIGNALPIN, 0);
    preservedstate = state;
  }
}
