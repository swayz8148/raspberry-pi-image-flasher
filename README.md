# Raspberry Pi Image Flasher

This Python script allows you to download and flash Raspberry Pi images onto an SD card with ease. It supports various Raspberry Pi distributions and provides a simple command-line interface for selecting the desired image.

## Prerequisites

Before running the script, ensure you have the following prerequisites installed:

- Python 3
- `aria2c` (for downloading images)
- `pv` (for progress visualization during flashing)

You can install `aria2c` and `pv` using your package manager or another suitable method.

## Installation

1. Clone this repository to your local machine:

```bash
git clone https://github.com/swayz8148/raspberry-pi-image-flasher.git
```

2. Navigate to the cloned directory:
```bash
cd ISO_Flash
```

## Usage

1. Run the script:

```bash
sudo python image_flasher.py
```

2. Follow the on-screen instructions to select the Raspberry Pi distribution and image file you want to flash onto the SD card.

3. Insert your SD card and follow the prompts to format and flash the image onto the card.

4. Once the process is complete, your SD card will be ready for use with your Raspberry Pi.

## Supported Raspberry Pi Distributions

- Raspbian Desktop
- Raspbian Desktop Full
- Raspbian Lite
- Ubuntu Server LTS for Pi 4
- Ubuntu Server for Pi 5
- DietPi

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
