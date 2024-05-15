import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image
import pytesseract
import re

# Configure the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\baha9\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Set to track processed images
processed_images = set()

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
            print(f'+++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print(f'New image detected: {image_name}')
            # Retry mechanism to ensure the file is completely written
            for _ in range(10):
                if os.path.exists(event.src_path):
                    process_image(event.src_path)
                    break
                time.sleep(1)
            else:
                print(f'File not found after multiple attempts: {event.src_path}')
            print(f'+++++++++++++++++++++++++++++++++++++++++++++++++++++++')

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
            print('No question found in the image.')
            return
        
        # Remove the first two characters from each response
        responses = [response[2:] for response in responses if len(response) > 2]
        
        # Create the dictionary
        result = {'Question': question_text}
        for idx, response in enumerate(responses):
            result[f'Response {idx + 1}'] = response
        
        # Print the result
        print(f'The question is: {result["Question"]}')
        print('The available options are:')
        for idx, response in enumerate(responses):
            print(f'  Option {idx + 1}: {response}')
        print(f'+++++++++++++++++++++++++++++++++++++++++++++++++++++++')

    except Exception as e:
        print(f'Failed to process image {image_path}: {e}')

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_folder = os.path.join(script_dir, 'screenshots')
    
    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, path=image_folder, recursive=False)
    observer.start()
    
    print(f'Started monitoring {image_folder} for new images.')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
