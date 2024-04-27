from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress
from urllib.parse import urlparse
from pathlib import Path
import concurrent.futures
import subprocess
import os
import requests
from datetime import datetime

console = Console()

partition = "/dev/mmcblk0"
download_dir = "./ISO"

IMAGES = {
    "Kali Linux": "https://kali.download/arm-images/kali-2024.1/kali-linux-2024.1-raspberry-pi5-arm64.img.xz",
}

PI_IMAGES = {
    "Raspbian Desktop": "https://downloads.raspberrypi.com/raspios_armhf/images/raspios_armhf-2024-03-15/2024-03-15-raspios-bookworm-armhf.img.xz",
    "Raspbian Desktop Full": "https://downloads.raspberrypi.com/raspios_full_armhf/images/raspios_full_armhf-2024-03-15/2024-03-15-raspios-bookworm-armhf-full.img.xz",
    "Raspbian Lite": "https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2024-03-15/2024-03-15-raspios-bookworm-armhf-lite.img.xz",
    "Ubuntu Server LTS Pi4": "https://cdimage.ubuntu.com/releases/22.04.4/release/ubuntu-22.04.4-preinstalled-server-arm64+raspi.img.xz?_gl=1*1b5ic9m*_gcl_au*NzU3MjM0MDYuMTcxMTczMjY5Nw..&_ga=2.263526153.483009528.1711851402-1604720038.1711732675",
    "Ubuntu Server Pi5": "https://cdimage.ubuntu.com/releases/23.10/release/ubuntu-23.10-preinstalled-server-arm64+raspi.img.xz?_gl=1*1raez99*_gcl_au*NzU3MjM0MDYuMTcxMTczMjY5Nw..&_ga=2.200611883.483009528.1711851402-1604720038.1711732675",
    "DietPi": "https://dietpi.com/downloads/images/testing/DietPi_RPi5-ARMv8-Bookworm.img.xz"
}

def check_ISO_dir():
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)


def check_dependencies():
    try:
        subprocess.run(["which", "aria2c"], check=True)
        subprocess.run(["which", "pv"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(Panel(f"[bold red]An error occurred: {e}[/bold red]"))
        exit(1)


def check_root():
    if os.geteuid() != 0:
        console.print(Panel("[bold red]This script must be run as root.[/bold red]"))
        exit(1)


def check_sd_card():
    try:
        subprocess.run(["lsblk", partition], check=True)
    except subprocess.CalledProcessError as e:
        console.print(Panel(f"[bold red]An error occurred: {e}[/bold red]"))
        exit(1)


def format_sd_card():
    try:
        console.clear
        console.print(Panel("[bold cyan]Formatting SD Card...[/bold cyan]"))
        mount_check = subprocess.run(["mountpoint", "-q", partition])
        if mount_check.returncode == 0:
            subprocess.run(["sudo", "umount", partition], check=True)
        subprocess.run(
            ["sudo", "parted", "--script", partition, "mklabel", "msdos"], check=True
        )
        subprocess.run(
            [
                "sudo",
                "parted",
                "--script",
                partition,
                "mkpart",
                "primary",
                "fat32",
                "1MiB",
                "100%",
            ],
            check=True,
        )
        subprocess.run(["sudo", "mkfs.vfat", "-I", "-F", "32", partition], check=True)
    except subprocess.CalledProcessError as e:
        console.print(Panel(f"[bold red]An error occurred: {e}[/bold red]"))
        exit(1)


def download_image(img_name, img_url):
    console.clear()
    file_ext = urlparse(img_url).path.split(".")[-1]
    img_file = os.path.join(download_dir, img_name + "." + file_ext)
    if os.path.exists(img_file):
        console.print(Panel(f"[bold yellow]{img_file} already exists.[/bold yellow]"))
        user_input = Prompt.ask(
            "The image could be outdated. Do you want to download it again?",
            choices=["y", "n"],
            default="n",
        )
        if user_input.lower() != "y":
            return img_file
        console.print(f"Removing the old image file {img_file}...", style="bold yellow")
        os.remove(img_file)
    console.print(f"Downloading {img_file}...", style="bold green")
    subprocess.run(
        ["aria2c", "-x16", "-s16", "-k1M", "-o", img_file, img_url], check=True
    )
    console.clear()
    return img_file


def flash_image(img_file):
    console.clear()
    console.print(
        Panel(f"[bold cyan]Flashing {img_file} onto the SD card...[/bold cyan]")
    )
    if img_file.endswith(".xz"):
        subprocess.run(
            f'xzcat "{img_file}" | pv | sudo dd of={partition} bs=4M',
            shell=True,
            check=True,
        )
    elif img_file.endswith(".tar.xz"):
        img_file_extracted = img_file.replace(".tar.xz", ".img")
        subprocess.run(
            f'tar -xf "{img_file}" -O > "{img_file_extracted}"',
            shell=True,
            check=True,
        )
        subprocess.run(
            f'sudo dd if="{img_file_extracted}" of={partition} bs=4M',
            shell=True,
            check=True,
        )
    elif img_file.endswith(".raw.xz"):
        img_file_extracted = img_file.replace(".raw.xz", ".img")
        subprocess.run(
            f'xzcat "{img_file}" > "{img_file_extracted}"', shell=True, check=True
        )
        subprocess.run(
            f'sudo dd if="{img_file_extracted}" of={partition} bs=4M',
            shell=True,
            check=True,
        )
    elif img_file.endswith(".iso"):
        subprocess.run(
            f'sudo dd if="{img_file}" of={partition} bs=4M', shell=True, check=True
        )



def main():
    while True:
        try:
            console.clear()
            console.print("Please select an option:", style="bold green")
            console.print("1) Supported [green] Raspberry PI Distros [/green]")
            console.print("2) Unsupported [yellow] Raspberry Pi Distros [/yellow]")
            console.print("3) Exit")
            choice = Prompt.ask(
                "Please enter your choice:", choices=["1", "2", "3"], default="1"
            )
            choice = int(choice)
            if choice == 1:
                console.clear()
                console.print(
                    "Please select an image file to download and flash onto the SD card:",
                    style="bold yellow",
                )
                for i, img_name in enumerate(PI_IMAGES.keys(), start=1):
                    console.print(f"{i}) {img_name}")
                console.print(f"{i+1}) Back")
                choice = Prompt.ask(
                    "Please enter your choice:",
                    choices=[str(i) for i in range(1, len(PI_IMAGES) + 2)],
                    default="1",
                )
                choice = int(choice) - 1
                if choice == len(PI_IMAGES):
                    console.clear()
                    continue
                img_name = list(PI_IMAGES.keys())[choice]
                img_url = PI_IMAGES[img_name]
            elif choice == 2:
                console.clear()
                console.print(
                    "Please select an image file to download and flash onto the SD card:",
                    style="bold green",
                )
                for i, img_name in enumerate(IMAGES.keys(), start=1):
                    console.print(f"{i}) {img_name}")
                console.print(f"{i+1}) Back")
                choice = Prompt.ask(
                    "Please enter your choice:",
                    choices=[str(i) for i in range(1, len(IMAGES) + 2)],
                    default="1",
                )
                choice = int(choice) - 1
                if choice == len(IMAGES):
                    console.clear()
                    continue
                img_name = list(IMAGES.keys())[choice]
                img_url = IMAGES[img_name]
                console.clear()
                console.print(
                    "Please select an image file to download and flash onto the SD card:",
                    style="bold green",
                )
                for i, img_name in enumerate(ARCH_IMAGES.keys(), start=1):
                    console.print(f"{i}) {img_name}")
                console.print(f"{i+1}) Back")
                choice = Prompt.ask(
                    "Please enter your choice:",
                    choices=[str(i) for i in range(1, len(ARCH_IMAGES) + 2)],
                    default="1",
                )
                choice = int(choice) - 1
                if choice == len(ARCH_IMAGES):
                    console.clear()
                    continue
                selected_image = list(ARCH_IMAGES.keys())[choice]
                if selected_image == "Archlinux ARM PI5":
                    archInstall()
            elif choice == 3:
                console.clear()
                break
            else:
                console.print(
                    "Invalid choice. Please enter 1, 2 or 3.", style="bold red"
                )
                continue

            with concurrent.futures.ThreadPoolExecutor() as executor:
                check_sd_card()
                check_dependencies()
                check_ISO_dir()
                check_root()
                img_file = download_image(img_name, img_url)
                format_sd_card()
                executor.submit(flash_image, img_file)

            console.print("Process completed.", style="bold green")
            exit(0)
        except Exception as e:
            console.print(f"An error occurred: {e}", style="bold red")
            exit(1)


if __name__ == "__main__":
    main()
