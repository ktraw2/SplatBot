import asyncio

''' Code from ktraw2's TVbot '''


async def run_command(*args):
    # Create subprocess
    process = await asyncio.create_subprocess_exec(
        *args,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE)
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    # Return stdout
    return stdout.decode().strip()


async def render_gif(image_base: str, gif_filename: str):
    await run_command('ffmpeg', '-framerate', '0.33', '-f', 'image2', '-i', image_base + '-%d.png', '-filter_complex', '[0:v] split [a][b];[a] palettegen=stats_mode=single [p]; [b][p] paletteuse=dither=none',
                      '-loglevel', 'warning', '-y', gif_filename)