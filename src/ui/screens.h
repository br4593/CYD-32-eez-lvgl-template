#ifndef EEZ_LVGL_UI_SCREENS_H
#define EEZ_LVGL_UI_SCREENS_H

#include <lvgl.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _objects_t {
    lv_obj_t *ehsi;
    lv_obj_t *obj0;
    lv_obj_t *compass_rose;
    lv_obj_t *hdg_drum;
    lv_obj_t *hdg_drum_label;
    lv_obj_t *overlay;
    lv_obj_t *hdg_debug;
    lv_obj_t *selected_heading;
    lv_obj_t *selected_heading_label;
    lv_obj_t *hdg_bug;
} objects_t;

extern objects_t objects;

enum ScreensEnum {
    SCREEN_ID_EHSI = 1,
};

void create_screen_ehsi();
void tick_screen_ehsi();

void tick_screen_by_id(enum ScreensEnum screenId);
void tick_screen(int screen_index);

void create_screens();


#ifdef __cplusplus
}
#endif

#endif /*EEZ_LVGL_UI_SCREENS_H*/