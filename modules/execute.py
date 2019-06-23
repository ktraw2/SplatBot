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


async def render_gif(image_base: str):
    await run_command('/Users/adamwang/Downloads/ffmpeg', '-r', '1', '-f', 'image2', '-i', image_base + '-%d.png',
                      '-r', '0.33', '-s', '848x480', image_base + '.gif')
