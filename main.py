from cryptography.fernet import InvalidToken
from cryptography.fernet import Fernet

import pyautogui
import time

from collections import defaultdict
from PIL import Image

import subprocess
from multiprocessing import Process
import vlc

from io import BytesIO
import tempfile
import base64
import hashlib

def password_to_key(password: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def track(path):
    player = vlc.MediaPlayer(path)

    # play the audio
    player.play()

    # keep the script running while the audio plays
    time.sleep(5)  # initial delay to start playing

    # check if still playing and keep the script alive
    while player.is_playing():
        time.sleep(1)

def open_wnd():
    # open mspain
    subprocess.Popen(["mspaint"])

    # wait some time for mspaint to start
    time.sleep(3)

    # maximize window
    pyautogui.hotkey("alt", "space")
    time.sleep(1)
    pyautogui.press("x")

def main():
    # open input image and convert to 16 colors palette
    with open("00.data", "rb") as f:
        encrypted_data = f.read()

    decrypted_data = None
    while decrypted_data is None:
        try:
            password = input("Contraseña:")
            key = password_to_key(password)
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
        except InvalidToken:
            print("Incorrecto!")


    image = (
        Image.open(BytesIO(decrypted_data)).reduce(2).quantize(colors=16).convert("RGB")
    )

    with open("01.data", "rb") as f:
        encrypted_data = f.read()

    decrypted_track = fernet.decrypt(encrypted_data)

    open_wnd()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        temp_audio_file.write(decrypted_track)
        temp_audio_file_path = temp_audio_file.name

    p = Process(name="track", target=track, args=(temp_audio_file_path,))
    p.start()

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
    component_delay = 0.01
    line_delay = 0.001

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

    p.join()


if __name__ == "__main__":
    # p = Process(name="track", target=test)
    # p.start()
    main()
    # p.join()
