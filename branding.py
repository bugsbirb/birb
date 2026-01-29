import os
import re
import logging

logger = logging.getLogger(__name__)

def ClearEmojis(condition, folder_path):
    if condition:
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if file_path.endswith('branding.py'):  
                    continue
                
                if file_name.endswith('.py'):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    new_content = re.sub(r'<:[a-zA-Z0-9_]+:[0-9]+>', '', content)
                    new_content = re.sub(r'<a:[a-zA-Z0-9_]+:[0-9]+>', '', new_content)
                    new_content = re.sub(r'emoji\s*=\s*""', 'emoji = None', new_content)
                    new_content = re.sub(r'emoji\s*=\s*"<\s*:[a-zA-Z0-9_]+:[0-9]+\s*>"', 'emoji = None', new_content)
                    new_content = re.sub(r'emoji\s*=\s*"<\s*a:[a-zA-Z0-9_]+:[0-9]+\s*>"', 'emoji = None', new_content)

                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        logger.info(f"Updated file: {file_path}")
                    else:
                        logger.info(f"No changes made in {file_path}")


