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
uint32_t active_theme_index = 0;

void create_screen_ehsi() {
    lv_obj_t *obj = lv_obj_create(0);
    objects.ehsi = obj;
    lv_obj_set_pos(obj, 0, 0);
    lv_obj_set_size(obj, 240, 320);
    {
        lv_obj_t *parent_obj = obj;
        {
            lv_obj_t *obj = lv_obj_create(parent_obj);
            objects.obj0 = obj;
            lv_obj_set_pos(obj, 0, 0);
            lv_obj_set_size(obj, 240, 270);
            lv_obj_set_style_bg_color(obj, lv_color_hex(0xff000000), LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_border_color(obj, lv_color_hex(0xff000000), LV_PART_MAIN | LV_STATE_DEFAULT);
            lv_obj_set_style_radius(obj, 0, LV_PART_MAIN | LV_STATE_DEFAULT);
            {
                lv_obj_t *parent_obj = obj;
                {
                    // compass_rose
                    lv_obj_t *obj = lv_image_create(parent_obj);
                    objects.compass_rose = obj;
                    lv_obj_set_pos(obj, 10, 25);
                    lv_obj_set_size(obj, 190, 190);
                    lv_image_set_src(obj, &img_compass_rose);
                    lv_image_set_scale(obj, 200);
                }
                {
                    // hdg_drum
                    lv_obj_t *obj = lv_image_create(parent_obj);
                    objects.hdg_drum = obj;
                    lv_obj_set_pos(obj, 89, -14);
                    lv_obj_set_size(obj, 35, 34);
                    lv_image_set_src(obj, &img_hdg_drum);
                    lv_image_set_scale(obj, 100);
                    {
                        lv_obj_t *parent_obj = obj;
                        {
                            // hdg_drum_label
                            lv_obj_t *obj = lv_label_create(parent_obj);
                            objects.hdg_drum_label = obj;
                            lv_obj_set_pos(obj, 5, 7);
                            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
                            lv_obj_set_style_text_color(obj, lv_color_hex(0xffffffff), LV_PART_MAIN | LV_STATE_DEFAULT);
                            lv_obj_set_style_text_font(obj, &lv_font_montserrat_12, LV_PART_MAIN | LV_STATE_DEFAULT);
                            lv_label_set_text(obj, "Text");
                        }
                    }
                }
                {
                    // overlay
                    lv_obj_t *obj = lv_image_create(parent_obj);
                    objects.overlay = obj;
                    lv_obj_set_pos(obj, -15, 0);
                    lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
                    lv_image_set_src(obj, &img_overlay);
                }
            }
        }
        {
            // HDG_debug
            lv_obj_t *obj = lv_label_create(parent_obj);
            objects.hdg_debug = obj;
            lv_obj_set_pos(obj, 0, 280);
            lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
            lv_label_set_text(obj, "HDG: ");
        }
        {
            // selected_heading
            lv_obj_t *obj = lv_image_create(parent_obj);
            objects.selected_heading = obj;
            lv_obj_set_pos(obj, 165, 245);
            lv_obj_set_size(obj, 75, 25);
            lv_image_set_src(obj, &img_selected_heading);
            lv_image_set_scale(obj, 155);
            {
                lv_obj_t *parent_obj = obj;
                {
                    // selected_heading_label
                    lv_obj_t *obj = lv_label_create(parent_obj);
                    objects.selected_heading_label = obj;
                    lv_obj_set_pos(obj, 23, 5);
                    lv_obj_set_size(obj, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
                    lv_obj_set_style_text_color(obj, lv_color_hex(0xff00ffff), LV_PART_MAIN | LV_STATE_DEFAULT);
                    lv_label_set_text(obj, "Text");
                }
            }
        }
        {
            // hdg_bug
            lv_obj_t *obj = lv_image_create(parent_obj);
            objects.hdg_bug = obj;
            lv_obj_set_pos(obj, 0, 30);
            lv_obj_set_size(obj, 240, 240);
            lv_image_set_src(obj, &img_hdg_bug);
        }
    }
    
    tick_screen_ehsi();
}

void tick_screen_ehsi() {
}



typedef void (*tick_screen_func_t)();
tick_screen_func_t tick_screen_funcs[] = {
    tick_screen_ehsi,
};
void tick_screen(int screen_index) {
    tick_screen_funcs[screen_index]();
}
void tick_screen_by_id(enum ScreensEnum screenId) {
    tick_screen_funcs[screenId - 1]();
}

void create_screens() {
    lv_disp_t *dispp = lv_disp_get_default();
    lv_theme_t *theme = lv_theme_default_init(dispp, lv_palette_main(LV_PALETTE_BLUE), lv_palette_main(LV_PALETTE_RED), false, LV_FONT_DEFAULT);
    lv_disp_set_theme(dispp, theme);
    
    create_screen_ehsi();
}
