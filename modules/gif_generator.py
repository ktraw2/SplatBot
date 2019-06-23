import requests
import shutil
from modules.splatoon_rotation import SplatoonRotation
from modules.execute import render_gif
import datetime

'''
HOW TO IMPLEMENT:

1. Use async_client.py(?) to get images, name them whatever (<date>-<time>-<photo #>.png)
2. Use TVbot's execute.py (github.com/ktraw2/TVBot/blob/261a14c42f94d33128ec7fbdfd372c18593d1a04/modules/execute.py)
    to run ffmpeg via command in #cse-zombies-4-mod to make gif
3. Send photo over via stackoverflow.com/questions/52241051/i-want-to-let-my-discord-bot-send-images-gifs

** already implmented garbage collector in Splatbot.py **
'''


async def generate_gif(rotation_info: SplatoonRotation):

    if rotation_info.stage_a_image is None or rotation_info.stage_b_image is None:
        raise Exception("Files to generate gif does not exist")

    image_a = rotation_info.stage_a_image
    image_b = rotation_info.stage_b_image

    image_base = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    image_a_filename = image_base + "-1.png"
    image_b_filename = image_base + "-2.png"

    r = requests.get(image_a, stream=True,
                     headers={'User-agent': 'SplatBot BETA TEST/1.0 Github: github.com/ktraw2/SplatBot'})
    if 200 <= r.status_code < 300:
        with open(image_a_filename, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    else:
        raise Exception("File %s was not saved", image_a_filename)

    r = requests.get(image_b, stream=True,
                     headers={'User-agent': 'SplatBot BETA TEST/1.0 Github: github.com/ktraw2/SplatBot'})
    if 200 <= r.status_code < 300:
        with open(image_b_filename, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    else:
        raise Exception("File %s was not saved", image_b_filename)

    await render_gif(image_base)

    return image_base + ".gif"

