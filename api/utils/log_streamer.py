import asyncio


# Async generator to yield log lines
async def log_streamer(file_path: str):
    with open(file_path, "r") as f:
        # Go to the end of the file
        f.seek(0, 2)
        while True:
            # Read any new lines
            line = f.readline()
            if line:
                yield line
            else:
                # If no new lines, sleep for a short time
                await asyncio.sleep(0.1)
