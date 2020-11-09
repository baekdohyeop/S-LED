#include <Adafruit_NeoPixel.h>

#define PIN 5
#define NUM_LEDS 144
#define BRIGHTNESS 50

int effect_buffer[50] = { 0, };
int prevRGB[3] = { 0, 0, 0 };
int responsiveRGB[3] = { 0, 0, 0};
int responsiveRGB_Cursor = 0;
int responsiveRGB_Count = 0;
int cycle = 0;
int effects_remain = 0;
int mode = 0;
int volume = 0;
int volume_len = 0;

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, PIN, NEO_GRBW + NEO_KHZ800);

int flag_checker(char flag){
   if(flag == '>'){
      mode++;
      if(mode == 3){
        mode = 0;
      }
      Serial.print('>');
      return 1;
    } else if(flag == '<'){
      mode--;
      if(mode == -1){
        mode = 2;
      }
      Serial.print('<');
      return 1;
    } else if('a' <= flag && flag <= 'z'){
      effect_buffer[effects_remain++] = (flag - 'a') * 100 + 40;
      return 2;
    } else if('0' <= flag && flag <= '9'){
      return 3;
    } else{
      return 0;
    }
}

void soundReactiveMode() {
  int volume_temp = 0;
  volume_len = 0;
  
  while(Serial.available()){
    int flag_case;
    char flag[2];

    flag[0] = Serial.read();
    flag_case = flag_checker(flag[0]);

    if(flag_case == 0){
      break;
    } else if(flag_case == 1){
      continue;
    }

    int temp = atoi(flag);

    volume_temp = volume_temp * 10 + temp;
    volume_len++;

    if(volume_len == 2){
      volume = volume_temp;
    }
  }

  for(uint16_t i=0; i<strip.numPixels(); i++) {
    if (i <= strip.numPixels()/2 - volume || strip.numPixels()/2 + volume <= i){
      strip.setPixelColor(i, strip.Color(0, 0, 0));
    } else{
      strip.setPixelColor(i, Wheel(((i * 256 / strip.numPixels()) + cycle) & 255));
    }
  }
  cycle++;
  if(cycle == 256){
    cycle = 0;
  }
  
  effect_checker();
  strip.show();
}

void effect_checker(){
  int idx = 0;
  
  while(effect_buffer[idx]){
    int effect = effect_buffer[idx] / 100;
    
    effects(effect, effect_buffer[idx] % 100);
    effect_buffer[idx]--;
    
    if(effect_buffer[idx] % 100 == 0){
      int temp_idx = idx;
      
      while(effect_buffer[idx]){
        effect_buffer[idx] = effect_buffer[idx + 1];
        idx++;
      }
      
      idx = temp_idx;
      effects_remain--;
    } else {
      idx++;
    }
  }
}

void effects(int type, int stage) {
  switch(type){
    case 0:{
      for(int i = 0; i < strip.numPixels(); i++){
        randomSeed(analogRead(0));
        
        if (random(0, 10) >= 9){
          strip.setPixelColor(i, strip.Color(random(100, 255), random(100, 255), random(100, 255)));
        }
      }
      break;
    }
    case 1:{
      for(int i = 0; i < strip.numPixels(); i++){
        float temp = 40 - stage;
        if (temp > 20){
          temp = 40 - temp;
        }

        float dim = temp / 20;
        strip.setPixelColor(i, strip.Color((int)(255 * dim), 0, 0));
      }
      break;
    }
    case 2:{
      for(int i = 0; i < strip.numPixels(); i++){
        float temp = 40 - stage;
        if (temp > 20){
          temp = 40 - temp;
        }

        float dim = temp / 20;
        strip.setPixelColor(i, strip.Color(0, (int)(255 * dim), 0));
      }
      break;
    }
    case 3:{
      for(int i = 0; i < strip.numPixels(); i++){
        float temp = 40 - stage;
        if (temp > 20){
          temp = 40 - temp;
        }

        float dim = temp / 20;
        strip.setPixelColor(i, strip.Color(0, 0, (int)(255 * dim)));
      }
      break;
    }
    case 4:{
      for(int i = 0; i < strip.numPixels(); i++){
        float temp = 40 - stage;
        if (temp > 20){
          temp = 40 - temp;
        }

        float dim = temp / 20;
        strip.setPixelColor(i, strip.Color((int)(255 * dim), (int)(255 * dim), (int)(255 * dim)));
      }
      break;
    }
  }
}

void Rainbow() {
  while(Serial.available()){
    char flag = Serial.read();
    flag_checker(flag);
  }
  
  for(uint16_t i=0; i<strip.numPixels(); i++) {
      strip.setPixelColor(i, Wheel(((i * 256 / strip.numPixels()) + cycle) & 255));
  }
  
  effect_checker();
  strip.show();
  
  cycle++;
  if(cycle == 256){
    cycle = 0;
  }
}

uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3,0);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3,0);
  }
  WheelPos -= 170;
  return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0,0);
}

void responsiveRGB_Mode(){
  responsiveRGB_Count = 0;
  responsiveRGB_Cursor = 0;
  
  while(Serial.available()){
    char flag[2];
    int flag_case;
    
    flag[0] = Serial.read();
    flag_case = flag_checker(flag[0]);
    
    if(flag_case == 0){
      break;
    } else if(flag_case == 1){
      continue;
    }

    int temp = atoi(flag);
    
    responsiveRGB[responsiveRGB_Cursor] = (responsiveRGB[responsiveRGB_Cursor] * 10 + temp) % 1000;
    responsiveRGB_Count++;

    if(responsiveRGB_Count == 9){
      responsiveRGB_Count = 0;
      responsiveRGB_Cursor = 0;
      for(int i = 0; i < strip.numPixels(); i++){
        strip.setPixelColor(i, strip.Color(responsiveRGB[0], responsiveRGB[1], responsiveRGB[2]));
      }
      prevRGB[0] = responsiveRGB[0];
      prevRGB[1] = responsiveRGB[1];
      prevRGB[2] = responsiveRGB[2];
    } else if(responsiveRGB_Count % 3 == 0){
      responsiveRGB_Cursor++;
      if(responsiveRGB_Cursor == 3){
        responsiveRGB_Cursor = 0;
      }

      for(int i = 0; i < strip.numPixels(); i++){
        strip.setPixelColor(i, strip.Color(prevRGB[0], prevRGB[1], prevRGB[2]));
      }
      effect_checker();
      strip.show();
    }
    
    for(int i = 0; i < strip.numPixels(); i++){
      strip.setPixelColor(i, strip.Color(prevRGB[0], prevRGB[1], prevRGB[2]));
    }
    effect_checker();
    strip.show();
  }
}

void setup()
{
  Serial.begin(2000000);
  strip.setBrightness(BRIGHTNESS);
  strip.begin();
}

void loop(){
  if(mode == 0){
    responsiveRGB_Mode();
  } else if(mode == 1){
    Rainbow();
  } else if(mode == 2){
    soundReactiveMode();
  }
}
