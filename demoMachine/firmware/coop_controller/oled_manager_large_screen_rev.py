# oled_manager_large_screen_rev.py
#
# Copied from the home lab (pi_pico/controller_hat/) with one change: a `rotate`
# argument, passed through to the driver.
#
# rotate=0 is the verified value for this rig — bench-checked 2026-10-07, reads
# right-side up plugged straight into the hat's J1.
#
# The ESPHome coop build needs `rotation: 180°` for the SAME display in the SAME
# header, and that is a library difference, not a hardware one. SH1106
# orientation comes from two registers (segment remap and COM scan direction),
# and sh1106.py and ESPHome disagree about which combination counts as zero — so
# sh1106.py's rotate=0 is ESPHome's 180°. Expect that offset on any board in this
# family: MicroPython rotate = ESPHome rotation - 180.
#
# Eight 8px lines of the built-in 8x8 font. MicroPython's framebuf has no other
# font, which is why this shows eight small lines where the ESPHome version drew
# four large ones. Each line scrolls independently if it overflows 16 characters.

import asyncio
import time
from machine import Pin, SPI
import sh1106

# picow            HiLetgo 1.3 oled    https://seengreat.com/product/205/pico-expansion-plus
SPI1_tx_15 = 15  #   mosi(DIN)           TX
SPI1_sck_14 = 14  #   clk                 sck
SPI1_csn_13 = 13  #   cs                  cs
SPI1_rx_12 = 12  #   dc                  rx
SPI1_sck_26 = 26  #   res                 gp26


class OLEDManager:
    def __init__(self, spi_bus=1, mosi_pin=SPI1_tx_15, sck_pin=SPI1_sck_14, cs_pin=SPI1_csn_13,
                 dc_pin=SPI1_rx_12, res_pin=SPI1_sck_26, width=128, height=64, rotate=0):
        self.width = width
        self.height = height
        self.dc = Pin(dc_pin, Pin.OUT)
        self.res = Pin(res_pin, Pin.OUT)
        self.cs = Pin(cs_pin, Pin.OUT)
        # Hardware reset pulse (fixes the display coming up blank on a cold boot)
        self.res.value(0)
        time.sleep_ms(100)
        self.res.value(1)
        time.sleep_ms(100)
        self.spi = SPI(spi_bus, sck=Pin(sck_pin), mosi=Pin(mosi_pin), baudrate=4000000)
        self.oled = sh1106.SH1106_SPI(self.width, self.height, self.spi, self.dc, self.res,
                                      self.cs, rotate=rotate)
        self.oled.contrast(50)  # Scale 0-255. 50 is plenty for indoors.
        self.lines = {}
        for i in range(1, 9):
            line_id = f"line{i}"
            self.lines[line_id] = {
                "text": "", "active_text": "", "x": 0, "y": (i - 1) * 8, "scrolling": False
            }

    def set_line(self, line_id, text, scrolling=False):
        """Updates line data without triggering new tasks."""
        if line_id in self.lines:
            if self.lines[line_id]["text"] != text:
                self.lines[line_id]["text"] = text
                self.lines[line_id]["active_text"] = text
                self.lines[line_id]["x"] = 0
            self.lines[line_id]["scrolling"] = scrolling

    async def _scroll_worker(self, line_id, pause_time=2.0):
        """Persistent worker: stays alive forever and monitors its assigned line."""
        while True:
            line = self.lines[line_id]
            text_width_px = len(line["text"]) * 8

            # If not scrolling or text is short, stay idle
            if not line["scrolling"] or text_width_px <= self.width:
                line["x"] = 0
                line["active_text"] = line["text"]
                await asyncio.sleep_ms(250)
                continue

            # Reset for a new scroll cycle
            line["active_text"] = line["text"]
            line["x"] = 0
            await asyncio.sleep(pause_time)

            stop_x = self.width - text_width_px
            current_text = line["text"]

            # Perform scroll
            for x in range(0, stop_x - 1, -1):
                if line["text"] != current_text:  # Text changed during scroll
                    break
                line["x"] = x
                await asyncio.sleep_ms(40)

            if line["text"] == current_text:
                await asyncio.sleep(pause_time)

    async def _master_render(self, fps=15):
        """Efficient rendering loop with error handling."""
        render_delay = 1000 // fps
        while True:
            try:
                self.oled.fill(0)
                for line_id in self.lines:
                    l = self.lines[line_id]
                    if l["active_text"]:
                        self.oled.text(l["active_text"], l["x"], l["y"])
                self.oled.show()
            except Exception as e:
                print(f"OLED Hardware Error: {e}")
            await asyncio.sleep_ms(render_delay)

    async def start(self):
        """Starts the master renderer and one worker per line."""
        asyncio.create_task(self._master_render())
        for i in range(1, 9):
            asyncio.create_task(self._scroll_worker(f"line{i}"))

        while True:  # Keep the manager alive
            await asyncio.sleep(60)

    async def show_splash(self, line1, line2, line3, delay=5):  # blocking on purpose
        self.oled.fill(0)
        self.oled.text(line1, 0, 9)
        self.oled.text(line2, 0, 24)
        self.oled.text(line3, 0, 50)
        self.oled.show()
        time.sleep(delay)
        self.oled.fill(0)
        self.oled.show()


async def main():
    oled_mgr = OLEDManager()
    await oled_mgr.show_splash("oled_manager", "Version 1.0", "Test oled :-)", delay=4)
    oled_mgr.oled.fill(0)


if __name__ == "__main__":
    asyncio.run(main())
