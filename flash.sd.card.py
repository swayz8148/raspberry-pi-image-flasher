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
    "Raspbian Desktop": "https://downloads.raspberrypi.com/raspios_armhf/images/raspios_armhf-2024-03-15/2024-03-15-raspios-bookworm-armhf.img.xz",
    "Raspbian Desktop Full": "https://downloads.raspberrypi.com/raspios_full_armhf/images/raspios_full_armhf-2024-03-15/2024-03-15-raspios-bookworm-armhf-full.img.xz",
    "Raspbian Lite": "https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2024-03-15/2024-03-15-raspios-bookworm-armhf-lite.img.xz",
    "Kali Linux ARM": "https://kali.download/arm-images/kali-2024.1/kali-linux-2024.1-raspberry-pi5-arm64.img.xz",
    "Ubuntu Server": "https://cdimage.ubuntu.com/releases/23.10/release/ubuntu-23.10-preinstalled-server-arm64+raspi.img.xz?_gl=1*6gsnu2*_gcl_au*NzY3MzA1NzkxLjE3MTE1ODAwMjc.&_ga=2.62749164.1374437728.1711580021-2082403470.1711580021",
    "Fedora Server 39": "https://download.fedoraproject.org/pub/fedora/linux/releases/39/Server/aarch64/images/Fedora-Server-39-1.5.aarch64.raw.xz",
}

BETA_IMAGES = {
    "Fedora Server 40": "https://fedora.mirrorservice.org/fedora/linux/releases/test/40_Beta/Server/aarch64/images/Fedora-Server-40_Beta-1.10.aarch64.raw.xz"
}

def is_link_up_to_date(url):
    response = requests.head(url)
    if 'Last-Modified' in response.headers:
        last_modified = response.headers['Last-Modified']
        last_modified_date = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S GMT')
        # If the resource was modified within the last 30 days, it's considered up-to-date
        if (datetime.now() - last_modified_date).days <= 30:
            return True
    return False

def format_sd_card():
    try:
        console.print(Panel("[bold cyan]Formatting SD Card...[/bold cyan]"))
        mount_check = subprocess.run(["mountpoint", "-q", partition])
        if mount_check.returncode == 0:
            subprocess.run(["sudo", "umount", partition], check=True)
        subprocess.run(["sudo", "parted", "--script", partition, "mklabel", "msdos"], check=True)
        subprocess.run(["sudo", "parted", "--script", partition, "mkpart", "primary", "fat32", "1MiB", "100%"], check=True)
        subprocess.run(["sudo", "mkfs.vfat", "-I", "-F", "32", partition], check=True)
    except subprocess.CalledProcessError as e:
        console.print(Panel(f"[bold red]An error occurred: {e}[/bold red]"))
        exit(1)

def download_image(img_name, img_url):
    path = urlparse(img_url).path
    img_file = os.path.join(download_dir, img_name + Path(path).suffix)
    if os.path.exists(img_file):
        console.print(Panel(f"[bold yellow]{img_file} already exists.[/bold yellow]"))
        user_input = Prompt.ask("The image could be outdated. Do you want to download it again?", choices=["y", "n"], default="n")
        if user_input.lower() != 'y':
            return img_file
        console.print(f"Removing the old image file {img_file}...", style="bold yellow")
        os.remove(img_file)
    console.print(f"Downloading {img_file}...", style="bold green")
    subprocess.run(["aria2c", "-x16", "-s16", "-k1M", "-o", img_file, img_url], check=True)
    console.clear()
    return img_file

def flash_image(img_file):
    console.print(Panel(f"[bold cyan]Flashing {img_file} onto the SD card...[/bold cyan]"))
    if img_file.endswith('.xz'):
        subprocess.run(f"xzcat \"{img_file}\" | pv | sudo dd of={partition} bs=4M", shell=True, check=True)
    else:
        subprocess.run(f"pv \"{img_file}\" | sudo dd of={partition} bs=4M", shell=True, check=True)

def main():
    while True:
        try:
            console.print("Please select an option:", style="bold green")
            console.print("1) LTS [green](stable and recommended for most users.)[/green]")
            console.print("2) Beta [red](bugs will happen in beta versions. Use at your own risk.)[/red]")
            console.print("3) Exit")
            choice = Prompt.ask("Please enter your choice:", choices=["1", "2", "3"], default="1")
            choice = int(choice)
            if choice == 1:
                console.clear()
                console.print("Please select an image file to download and flash onto the SD card:", style="bold green")
                for i, img_name in enumerate(IMAGES.keys(), start=1):
                    console.print(f"{i}) {img_name}")
                console.print(f"{i+1}) Back")
                choice = Prompt.ask("Please enter your choice:", choices=[str(i) for i in range(1, len(IMAGES)+2)], default="1")
                choice = int(choice) - 1
                if choice == len(IMAGES):
                    console.clear()
                    continue
                img_name = list(IMAGES.keys())[choice]
                img_url = IMAGES[img_name]
                if not is_link_up_to_date(img_url):
                    console.print(f"The image file {img_name} is not up-to-date. Please update the URL.", style="bold red")
                    continue
            elif choice == 2:
                console.clear()
                console.print("Please select a beta image file to download and flash onto the SD card:", style="bold green")
                for i, img_name in enumerate(BETA_IMAGES.keys(), start=1):
                    console.print(f"{i}) {img_name}")
                console.print(f"{i+1}) Back")
                choice = Prompt.ask("Please enter your choice:", choices=[str(i) for i in range(1, len(BETA_IMAGES)+2)], default="1")
                choice = int(choice) - 1
                if choice == len(BETA_IMAGES):
                    console.clear()
                    continue
                img_name = list(BETA_IMAGES.keys())[choice]
                img_url = BETA_IMAGES[img_name]
                if not is_link_up_to_date(img_url):
                    console.print(f"The image file {img_name} is not up-to-date. Please update the URL.", style="bold red")
                    continue
            elif choice == 3:
                console.clear()
                break
            else:
                console.print("Invalid choice. Please enter 1, 2 or 3.", style="bold red")
                continue

            with concurrent.futures.ThreadPoolExecutor() as executor:
                img_file = download_image(img_name, img_url)
                format_sd_card()
                executor.submit(flash_image, img_file)
            console.print("Process completed.", style="bold green")
        except Exception as e:
            console.print(f"An error occurred: {e}", style="bold red")
            exit(1)

if __name__ == "__main__":
    main()