"""Support code for handling device software"""

# -- Imports ------------------------------------------------------------------

from pathlib import Path

from icotest.cli.commander import Commander

# -- Functions ----------------------------------------------------------------


def upload_flash(chip: str, flash_location: str | Path):
    """Upload bootloader and application into node

    Args:

        chip:
            The name of the chip that should be flashed

        flash_location:
            The location of the flash image

    """

    image_filepath = Path(flash_location).expanduser().resolve()
    if not image_filepath.exists():
        raise FileNotFoundError(
            "Firmware file {image_filepath} does not exist"
        )
    if not image_filepath.is_file():
        raise FileNotFoundError(
            f"Firmware file {image_filepath} is not a file"
        )

    Commander().upload_flash(chip=chip, filepath=image_filepath)
