import os
import time
import subprocess
import webbrowser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image
import pytesseract
import re
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# List of required packages
required_packages = ['watchdog', 'pillow', 'pytesseract', 'colorama']

def install_packages(packages):
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(Fore.GREEN + f'Successfully installed {package}')
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f'Failed to install {package}: {e}')

def setup_environment():
    user_confirmation = input(Fore.CYAN + "Do you want to install the required packages? (yes/no): ").strip().lower()
    if user_confirmation == 'yes':
        install_packages(required_packages)
        print(Fore.YELLOW + "\nNote: You need to install a software called Tesseract OCR.")
        print(Fore.YELLOW + "After approving the installation of the software, your default browser will start downloading the app.\n")
        time.sleep(1)

    print(Fore.CYAN + "Opening browser to download Tesseract OCR...\n")
    time.sleep(1)
    webbrowser.open('https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe')
    input(Fore.CYAN + "\nPlease install Tesseract OCR and press Enter to continue...\n")
    
    tesseract_path = input(Fore.CYAN + "Enter the path to the Tesseract executable (e.g., C:\\Users\\baha9\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe): ").strip()
    
    # Ensure the tesseract path ends with the executable filename
    while not os.path.isfile(tesseract_path) or not tesseract_path.endswith("tesseract.exe"):
        print(Fore.RED + "The provided path is incorrect. Tesseract OCR is required to run this script.")
        tesseract_path = input(Fore.CYAN + "Please enter the correct path to the Tesseract executable (e.g., C:\\Users\\baha9\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe): ").strip()

    screenshot_folder = input(Fore.CYAN + "Enter the path to the screenshot folder (or press Enter to use the default 'screenshots' folder): ").strip()
    if not screenshot_folder:
        screenshot_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
        print(Fore.GREEN + f'Using default screenshot folder: {screenshot_folder}')
    elif not os.path.exists(screenshot_folder):
        print(Fore.RED + "The specified directory does not exist. Using default 'screenshots' folder.")
        screenshot_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
        print(Fore.GREEN + f'Using default screenshot folder: {screenshot_folder}')

    return tesseract_path, screenshot_folder

class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return None
        
        if event.src_path.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            # Ensure that the event is not triggered twice
            time.sleep(1)
            image_name = os.path.basename(event.src_path)
            if image_name in processed_images:
                return
            processed_images.add(image_name)
            print(Fore.YELLOW + f'+++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print(Fore.GREEN + f'New image detected: {image_name}')
            # Retry mechanism to ensure the file is completely written
            for _ in range(10):
                if os.path.exists(event.src_path):
                    try:
                        process_image(event.src_path)
                    except Exception as e:
                        print(Fore.RED + f'Failed to process image {event.src_path}: {e}')
                    break
                time.sleep(1)
            else:
                print(Fore.RED + f'File not found after multiple attempts: {event.src_path}')
            print(Fore.YELLOW + f'+++++++++++++++++++++++++++++++++++++++++++++++++++++++')

def process_image(image_path):
    try:
        # Use pytesseract to do OCR on the image
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        
        # Split the text into lines
        lines = text.split('\n')
        
        # Extract question and responses
        question_found = False
        question = []
        responses = []
        question_prefix_pattern = re.compile(r'^Question \d+ of \d+')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if question_prefix_pattern.match(line):
                question_found = True
                continue
            
            if question_found:
                question.append(line)
                if line.endswith('?'):
                    question_found = False
            else:
                responses.append(line)
        
        # Join the question lines
        question_text = ' '.join(question).strip()
        
        if not question_text:
            print(Fore.RED + 'No question found in the image.')
            return
        
        # Remove the first two characters from each response
        responses = [response[2:] for response in responses if len(response) > 2]
        
        # Create the dictionary
        result = {'Question': question_text}
        for idx, response in enumerate(responses):
            result[f'Response {idx + 1}'] = response
        
        # Print the result
        print(Fore.CYAN + f'The question is: {result["Question"]}')
        print(Fore.CYAN + 'The available options are:')
        for idx, response in enumerate(responses):
            print(Fore.YELLOW + f'  Option {idx + 1}: {response}')
        print(Fore.YELLOW + f'+++++++++++++++++++++++++++++++++++++++++++++++++++++++')

    except Exception as e:
        print(Fore.RED + f'Failed to process image {image_path}: {e}')

if __name__ == "__main__":
    import sys

    tesseract_path, screenshot_folder = setup_environment()
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, path=screenshot_folder, recursive=False)
    observer.start()
    
    print(Fore.CYAN + f'Started monitoring {screenshot_folder} for new images.')
    
    processed_images = set()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
