#include <string.h>

#include "screens.h"
#include "images.h"
#include "fonts.h"
#include "actions.h"
#include "vars.h"
#include "styles.h"
#include "ui.h"

#include <string.h>

objects_t objects;
lv_obj_t *tick_value_change_obj;

void create_screen_main() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.main = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 320, 240);
    {
        lv_obj_t *parent_obj = obj;
        {
            // screen1_btn
            lv_obj_t *obj = lv_btn_create(parent_obj);
            objects.screen1_btn = obj;
            lv_obj_set_pos(obj, 15, 95);
            lv_obj_set_size(obj, 100, 50);
            lv_obj_add_event_cb(obj, action_set_global_eez_event, LV_EVENT_RELEASED, (void *)0);
            {
                lv_obj_t *parent_obj = obj;
                {
                    lv_obj_t *obj = lv_label_create(parent_obj);
                    lv_obj_set_pos(obj, 0, 0);
                    lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
                    lv_label_set_text(obj, "Screen1");
                    lv_obj_set_style_align(obj, LV_ALIGN_CENTER, LV_PART_MAIN | LV_STATE_DEFAULT);
                }
            }
        }
        {
            lv_obj_t *obj = lv_label_create(parent_obj);
            lv_obj_set_pos(obj, 115, 36);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            lv_label_set_text(obj, "Main Screen");
        }
        {
            // led_btn
            lv_obj_t *obj = lv_btn_create(parent_obj);
            objects.led_btn = obj;
            lv_obj_set_pos(obj, 205, 95);
            lv_obj_set_size(obj, 100, 50);
            lv_obj_add_event_cb(obj, action_set_global_eez_event, LV_EVENT_RELEASED, (void *)0);
            {
                lv_obj_t *parent_obj = obj;
                {
                    // LED
                    lv_obj_t *obj = lv_label_create(parent_obj);
                    objects.led = obj;
                    lv_obj_set_pos(obj, 0, 0);
                    lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
                    lv_label_set_text(obj, "On/Off");
                    lv_obj_set_style_align(obj, LV_ALIGN_CENTER, LV_PART_MAIN | LV_STATE_DEFAULT);
                }
            }
        }
    }
}

void tick_screen_main() {
}

void create_screen_screen1() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.screen1 = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 320, 240);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_label_create(parent_obj);
            lv_obj_set_pos(obj, 109, 27);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            lv_label_set_text(obj, "This is Screen1");
        }
        {
            // back_btn
            lv_obj_t *obj = lv_btn_create(parent_obj);
            objects.back_btn = obj;
            lv_obj_set_pos(obj, 110, 95);
            lv_obj_set_size(obj, 100, 50);
            lv_obj_add_event_cb(obj, action_set_global_eez_event, LV_EVENT_RELEASED, (void *)0);
            {
                lv_obj_t *parent_obj = obj;
                {
                    lv_obj_t *obj = lv_label_create(parent_obj);
                    objects.obj0 = obj;
                    lv_obj_set_pos(obj, 0, 0);
                    lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
                    lv_label_set_text(obj, "Back");
                    lv_obj_add_event_cb(obj, action_set_global_eez_event, LV_EVENT_PRESSED, (void *)0);
                    lv_obj_set_style_align(obj, LV_ALIGN_CENTER, LV_PART_MAIN | LV_STATE_DEFAULT);
                }
            }
        }
    }
}

void tick_screen_screen1() {
}


void create_screens() {
    lv_disp_t *dispp = lv_disp_get_default();
    lv_theme_t *theme = lv_theme_default_init(dispp, lv_palette_main(LV_PALETTE_BLUE), lv_palette_main(LV_PALETTE_RED), false, LV_FONT_DEFAULT);
    lv_disp_set_theme(dispp, theme);
    
    create_screen_main();
    create_screen_screen1();
}

typedef void (*tick_screen_func_t)();

tick_screen_func_t tick_screen_funcs[] = {
    tick_screen_main,
    tick_screen_screen1,
};

void tick_screen(int screen_index) {
    tick_screen_funcs[screen_index]();
}
