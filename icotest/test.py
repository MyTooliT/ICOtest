# -- Imports ------------------------------------------------------------------

from asyncio import run

from icotronic.cmdline.commander import Commander

# -- Functions ----------------------------------------------------------------


async def test_power_usage():
    commander = Commander(serial_number=440069950, chip="BGM121A256V2")
    print(f"Power Usage: {commander.read_power_usage()} mW")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(test_power_usage())
