# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

import os
import shutil
import re
from datetime import datetime
from PIL import Image, ImageEnhance

# Configuration
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
# Calculate BASE_DATA_DIR from script location (scripts/ is in project root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BASE_DATA_DIR = os.path.join(PROJECT_ROOT, "copilot_data")
PROCESSED_DIR = os.path.join(BASE_DATA_DIR, "meter-photos/processed")
ARCHIVE_DIR = os.path.join(BASE_DATA_DIR, "meter-photos/archive")
MAX_SIZE = (1024, 1024)

def fetch_and_process_images():
    print(f"Scanning {DOWNLOADS_DIR} for meter reading folders...")
    
    current_month_folder = datetime.now().strftime("%Y-%m")
    target_processed_dir = os.path.join(PROCESSED_DIR, current_month_folder)
    os.makedirs(target_processed_dir, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # Regex for LINE download formats: DD/MM/YYYY, DD-MM-YYYY, etc.
    # Supports both AD (2026) and BE (2569) years.
    folder_pattern = re.compile(r'^(\d{1,2})[/\-._ ](\d{1,2})[/\-._ ](\d{4})(?: #\d+)?$')
    
    count = 0
    # Find matching folders in Downloads
    for item in os.listdir(DOWNLOADS_DIR):
        item_path = os.path.join(DOWNLOADS_DIR, item)
        if os.path.isdir(item_path) and folder_pattern.match(item):
            print(f"Found matching folder: {item}")
            # Identify unit_type: folders with #1, #2 etc are usually water
            unit_type = "water" if re.search(r'#\d+', item) else "electric"
            
            for file in os.listdir(item_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(item_path, file)
                    
                    try:
                        # 1. Enhance & Resize
                        with Image.open(img_path) as img:
                            # Convert to RGB if necessary (e.g. RGBA)
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                                
                            enhancer = ImageEnhance.Contrast(img)
                            enhanced_img = enhancer.enhance(1.3) # Boost contrast slightly more
                            
                            # Optional: Sharpening
                            # from PIL import ImageFilter
                            # enhanced_img = enhanced_img.filter(ImageFilter.SHARPEN)
                            
                            enhanced_img.thumbnail(MAX_SIZE)
                            
                            # 2. Extract Shop ID from filename
                            # LINE filenames are often like "V-A1_12345678.jpg" or just "V-A1.jpg"
                            # We take the part before the first underscore or dot
                            shop_id = re.split(r'[_.]', file)[0]
                            
                            new_filename = f"{shop_id}_{unit_type}.jpg"
                            
                            # 3. Save directly to processed dir
                            out_path = os.path.join(target_processed_dir, new_filename)
                            enhanced_img.save(out_path, "JPEG", quality=85)
                            print(f"  Processed: {file} -> {new_filename}")
                            count += 1
                    except Exception as e:
                        print(f"  Error processing {file}: {e}")
            
            # Move the original folder to archive
            try:
                # If archive already has a folder with same name, add timestamp
                archive_name = item
                if os.path.exists(os.path.join(ARCHIVE_DIR, archive_name)):
                    archive_name = f"{item}_{datetime.now().strftime('%H%M%S')}"
                
                shutil.move(item_path, os.path.join(ARCHIVE_DIR, archive_name))
                print(f"Moved {item} to archive.")
            except Exception as e:
                print(f"Error moving {item} to archive: {e}")

    print(f"Finished. Total images processed: {count}")

if __name__ == "__main__":
    fetch_and_process_images()
