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

import openpyxl
from openpyxl.drawing.image import Image
import shutil
import os

TEMPLATE_PATH = "/Users/hare/meen/testai-cowork/copilot_data/excel-files/template/รายงานมิเตอร์ น้ำไฟฟ้า ปี 2569.xlsx"
OUTPUT_PATH = "/Users/hare/meen/testai-cowork/copilot_data/excel-files/monthly/test_output_2026_06.xlsx"

def test_excel_automation():
    # 1. Load Workbook
    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    sheet = wb["ฟฟ ม.ค.69"] # Use a valid sheet
    
    # 2. Simulate finding a shop row (e.g., "V-A1") and modifying meter values
    row_idx = 10 # Mock row
    prev_meter_col = 'D'
    new_meter_col = 'E'
    
    # Move old value to previous column to check formula
    sheet[f"{prev_meter_col}{row_idx}"] = sheet[f"{new_meter_col}{row_idx}"].value
    
    # Insert new meter reading
    sheet[f"{new_meter_col}{row_idx}"] = 1205
    
    # 3. Embed an image
    mock_img_path = "/Users/hare/meen/testai-cowork/copilot_data/meter-photos/processed/mock_photo.jpg"
    if not os.path.exists(mock_img_path):
        from PIL import Image as PILImage
        img = PILImage.new('RGB', (100, 100), color = 'red')
        img.save(mock_img_path)
    
    if os.path.exists(mock_img_path):
        img = Image(mock_img_path)
        img.width, img.height = 100, 100 # Resize image
        sheet.add_image(img, f"Z{row_idx}") # Place image in column Z
    
    # 4. Save Workbook
    wb.save(OUTPUT_PATH)
    print(f"Saved test file to {OUTPUT_PATH}")

if __name__ == "__main__":
    test_excel_automation()
