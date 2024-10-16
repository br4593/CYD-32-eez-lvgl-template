#include <Arduino.h>
#include <TFT_eSPI.h>
#include <TAMC_GT911.h>
#include "touch.h"
#include "ui\ui.h"
#include <lvgl.h>

#define SCREEN_WIDTH 240
#define SCREEN_HEIGHT 320
#define LED_PIN 17





TFT_eSPI tft = TFT_eSPI(SCREEN_WIDTH, SCREEN_HEIGHT); /* TFT instance */
TAMC_GT911 tp = TAMC_GT911(TOUCH_SDA, TOUCH_SCL, TOUCH_INT, TOUCH_RST, TOUCH_WIDTH, TOUCH_HEIGHT);

extern lv_event_t g_eez_event;
extern bool g_eez_event_is_available;

// Touchscreen coordinates: (x, y) and pressure (z)
int x, y, z;

#define DRAW_BUF_SIZE (SCREEN_WIDTH * SCREEN_HEIGHT / 10 * (LV_COLOR_DEPTH / 8))
uint32_t draw_buf[DRAW_BUF_SIZE / 4];

// If logging is enabled, it will inform the user about what is happening in the library
void log_print(lv_log_level_t level, const char * buf) {
  LV_UNUSED(level);
  Serial.println(buf);
  Serial.flush();
}





// Get the Touchscreen data
void touchscreen_read(lv_indev_t * indev, lv_indev_data_t * data) {
    uint16_t touchX = 0, touchY = 0;

    //bool touched = false;//tft.getTouch( &touchX, &touchY, 600 );
    bool touched = tp.isTouched;//tft.getTouch( &touchX, &touchY, 600 );

    if( !touched )
    {
        data->state = LV_INDEV_STATE_REL;
    }
    else
    {
        data->state = LV_INDEV_STATE_PR;

     for (int i=0; i<tp.touches; i++)
     {
        /*Set the coordinates*/
        data->point.x = tp.points[i].x;
        data->point.y = tp.points[i].y;

        Serial.print( "Data x " );
        Serial.println( tp.points[i].x );

        Serial.print( "Data y " );
        Serial.println( tp.points[i].y );
     }
    }
}


void setup() {
  String LVGL_Arduino = String("LVGL Library Version: ") + lv_version_major() + "." + lv_version_minor() + "." + lv_version_patch();
  Serial.begin(115200);
  Serial.println(LVGL_Arduino);

tft.begin();
  tft.setRotation(3);

  
  // Start LVGL
  lv_init();

   lv_tick_set_cb((lv_tick_get_cb_t)millis);
  // Register print function for debugging
  lv_log_register_print_cb(log_print);

  Wire.begin(TOUCH_SDA, TOUCH_SCL);
  tp.begin();
  tp.setRotation(TOUCH_ROTATION);

  // Create a display object
  lv_display_t * disp;
  // Initialize the TFT display using the TFT_eSPI library
  disp = lv_tft_espi_create(SCREEN_WIDTH, SCREEN_HEIGHT, draw_buf, sizeof(draw_buf));
  lv_display_set_rotation(disp, LV_DISPLAY_ROTATION_270);
    
  // Initialize an LVGL input device object (Touchscreen)
  lv_indev_t * indev = lv_indev_create();
  lv_indev_set_type(indev, LV_INDEV_TYPE_POINTER);
  // Set the callback function to read Touchscreen input
  lv_indev_set_read_cb(indev, touchscreen_read);

  ui_init();

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
}

void loop() {
        
        tp.read();
  if (tp.isTouched){
    for (int i=0; i<tp.touches; i++){
      Serial.print("Touch ");Serial.print(i+1);Serial.print(": ");;
      Serial.print("  x: ");Serial.print(tp.points[i].x);
      Serial.print("  y: ");Serial.print(tp.points[i].y);
      Serial.print("  size: ");Serial.println(tp.points[i].size);
      Serial.println(' ');
    }
  }

  lv_task_handler();  // let the GUI do its work
  lv_tick_inc(5);     // tell LVGL how much time has passed
  delay(5);

  if (g_eez_event_is_available)
  {
    lv_obj_t *obj = lv_event_get_target_obj(&g_eez_event);
    Serial.printf("Recieved event from object %u\n", obj);
    g_eez_event_is_available = false;

    if (obj == objects.screen1_btn)
    {
      lv_scr_load(objects.screen1);
    }

    else if (obj == objects.back_btn)
    {
      lv_scr_load(objects.main);
    }

    else if (obj == objects.led_btn)
    {
      static boolean led_status = LOW;
      led_status = !led_status;
      Serial.println("LED toggled");
      digitalWrite(LED_PIN, led_status);

    }
  }

}