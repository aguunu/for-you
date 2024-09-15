import pyautogui
import time

from collections import defaultdict
from PIL import Image

import subprocess
import ctypes
from ctypes import wintypes

# windows API constants
SW_MAXIMIZE = 3

# config for windows API
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]

# open mspain
subprocess.Popen(["mspaint"])

# wait some time for mspaint to start
time.sleep(2)

# find mspaint window using default title ('Untitled - Paint')
hwnd = user32.FindWindowW(None, "Untitled - Paint")

# maximize window if found
if hwnd:
    user32.ShowWindow(hwnd, SW_MAXIMIZE)
else:
    print("MS Paint window not found.")

# open input image and convert to 16 colors palette
image = Image.open("input-image.png").reduce(2).quantize(colors=16).convert("RGB")

width, height = image.size

# all directions for flood fill algorithm
directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def flood_fill(image, start_coord, color, visited):
    stack = [start_coord]
    component = []

    while stack:
        x, y = stack.pop()
        if (x, y) not in visited and 0 <= x < width and 0 <= y < height:
            if image.getpixel((x, y)) == color:
                visited.add((x, y))
                component.append((x, y))

                for direction in directions:
                    nx, ny = x + direction[0], y + direction[1]
                    stack.append((nx, ny))

    return component


color_continuous_sets = defaultdict(list)
visited = set()

for y in range(height):
    for x in range(width):
        color = image.getpixel((x, y))
        if (x, y) not in visited:
            component = flood_fill(image, (x, y), color, visited)
            if component:
                color_continuous_sets[color].append(component)

# mspaint custom color pixel perfect
custom_color = (992, 70)


def change_color(red, green, blue):
    pyautogui.moveTo(custom_color[0], custom_color[1])
    pyautogui.click()
    pyautogui.press("tab", presses=7)

    args = [red, green, blue]
    for arg in args:
        pyautogui.typewrite(str(arg))
        pyautogui.press("tab")
    pyautogui.press("tab")
    pyautogui.press("enter")


# remove pyautogui default delay
pyautogui.PAUSE = 0.0

# screen offsets
offset_x = 250
offset_y = 250

# set custom delay
component_delay = 0.00000001
line_delay = 0.0000000001

for color, components in color_continuous_sets.items():
    print(f"Selecting color: {color}: {len(components)} pixels.")
    change_color(*color)
    time.sleep(component_delay)

    print(color)
    if color[0] == 255 and color[1] == 255 and color[2] == 255:
        continue

    for component in components:
        ys = {pixel[1] for pixel in component}

        time.sleep(component_delay)
        for y in ys:
            # get component x-axis pixels
            xs = [pixel[0] for pixel in component if pixel[1] == y]

            # sort x-axis pixels
            xs.sort()

            x0 = x1 = xs[0]

            for idx, x in enumerate(xs):
                if x == x0 + 1:
                    x1 = x
                else:
                    time.sleep(line_delay)
                    pyautogui.moveTo(offset_x + x0, offset_y + y)
                    pyautogui.mouseDown()
                    pyautogui.moveTo(offset_x + x1, offset_y + y)
                    pyautogui.mouseUp()

                    x0 = x1 = xs[idx]

            time.sleep(line_delay)
            pyautogui.moveTo(offset_x + x0, offset_y + y)
            pyautogui.mouseDown()
            pyautogui.moveTo(offset_x + x1, offset_y + y)
            pyautogui.mouseUp()
