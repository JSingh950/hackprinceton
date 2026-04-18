# SenseCAP — LVGL firmware

**Owner: Ariji.** Custom ESP-IDF + LVGL firmware for the SenseCAP Indicator, plus the wider hardware integration (Grove button/LED via the Pi's GPIO, cardboard enclosure, privacy-shutter servo, MLH hardware pickup). Ambient display: idle → listening → thinking → answer. Driven by JSON-lines over USB serial from the Pi.

> Jossue (team lead) owns Devpost, demo script, track submissions, and the overall pitch — ping him on anything that touches those.

---

## What "done" looks like by Friday 2 AM

- [ ] SenseCAP flashes and boots to the idle state without factory splash.
- [ ] All 4 states render correctly when driven from the Pi via `echo '{"state":"..."}' > /dev/ttyACM0`.
- [ ] Answer + alert states auto-dismiss back to idle after their timeout.
- [ ] If it's 10 PM Friday and serial isn't working — **stop, switch to the phone-stand fallback** (see bottom of this file). Don't burn Saturday on firmware.

## States

1. **Idle** — slow-breathing dot centered, "Rewind · watching" subtext.
2. **Listening** — pulsing ring (faster than idle), "listening" subtext. *Pi triggers this when Grove button is pressed.*
3. **Thinking** — spinner, "thinking…" subtext. *Pi triggers when LLM call is in flight.*
4. **Answer** — 1–2 wrapped lines of large text. Auto-dismiss to idle after 15 s.

Optional 5th state: **Alert** — red accent, urgent title, 10s auto-dismiss. Used when Eragon agent fires a med-overdue alert.

## Serial Protocol (Pi → SenseCAP)

JSON-lines over `/dev/ttyACM0` at 115200 baud:

```json
{"state": "idle"}
{"state": "listening"}
{"state": "thinking"}
{"state": "answer", "text": "On the kitchen counter, 47 min ago."}
{"state": "alert", "text": "Evening meds 2h overdue"}
{"state": "shutter_closed"}
```

## Build Path

1. **Base:** clone `https://github.com/Seeed-Studio/sensecap-indicator-examples`, start from the `lvgl_demos/` folder. Strip all sample apps. One `lv_obj_t *root` container, full screen.

2. **Create 4 LVGL widgets (all hidden by default except idle):**
   - `idle_dot` — `lv_obj_t` circle, animated size 24→32→24 px over 2s loop (`lv_anim_t`).
   - `listening_ring` — `lv_arc_create()` with indicator color + rotating animation, faster.
   - `thinking_spinner` — `lv_spinner_create(root, 1000, 60)`.
   - `answer_label` — `lv_label_create()`, `lv_label_set_long_mode(LV_LABEL_LONG_WRAP)`, 32pt font, center-aligned.

3. **State switch function:**
   ```c
   typedef enum { ST_IDLE, ST_LISTENING, ST_THINKING, ST_ANSWER, ST_ALERT } rewind_state_t;

   void rewind_set_state(rewind_state_t s, const char *text) {
     lv_obj_add_flag(idle_dot,        LV_OBJ_FLAG_HIDDEN);
     lv_obj_add_flag(listening_ring,  LV_OBJ_FLAG_HIDDEN);
     lv_obj_add_flag(thinking_spinner,LV_OBJ_FLAG_HIDDEN);
     lv_obj_add_flag(answer_label,    LV_OBJ_FLAG_HIDDEN);
     switch (s) {
       case ST_IDLE:      lv_obj_clear_flag(idle_dot, LV_OBJ_FLAG_HIDDEN); break;
       case ST_LISTENING: lv_obj_clear_flag(listening_ring, LV_OBJ_FLAG_HIDDEN); break;
       case ST_THINKING:  lv_obj_clear_flag(thinking_spinner, LV_OBJ_FLAG_HIDDEN); break;
       case ST_ANSWER:
       case ST_ALERT:
         lv_label_set_text(answer_label, text);
         lv_obj_clear_flag(answer_label, LV_OBJ_FLAG_HIDDEN);
         schedule_auto_idle(s == ST_ALERT ? 10000 : 15000);
         break;
     }
   }
   ```

4. **Serial reader task:** FreeRTOS task on `UART0`. Accumulate bytes until `\n`, parse JSON with cJSON, call `rewind_set_state()`.

## Fallback if flashing eats >2 hours

Time-box strictly. If at 10 PM Friday the SenseCAP isn't responding to serial commands, abandon the custom firmware:

- Leave SenseCAP on its factory splash as a passive "device is powered" indicator.
- Prop a phone in a small stand next to the Rewind device.
- Phone runs a stripped-down mobile web view of `/status` on the Pi (Jeeyan can add this page in 20 min).
- Display idle/listening/thinking/answer states identically. Judges cannot tell the difference.

## Test from the Pi

```bash
# Assuming /dev/ttyACM0 is SenseCAP
stty -F /dev/ttyACM0 115200
echo '{"state":"listening"}' > /dev/ttyACM0
sleep 2
echo '{"state":"thinking"}' > /dev/ttyACM0
sleep 2
echo '{"state":"answer","text":"On the table."}' > /dev/ttyACM0
sleep 6
echo '{"state":"idle"}' > /dev/ttyACM0
```

If all four renders correctly → firmware is done. Move on.
