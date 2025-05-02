import os
import shutil

source_folder = "documents/immigration_docs/usa"
files = os.listdir(source_folder)

for file in files:
    if file.endswith('.pdf'):
        form_name = file.replace('INSTRUCTIONS.pdf', '').replace('.pdf', '').lower().replace('-', '_')
        new_folder = os.path.join(source_folder, form_name)
        if not os.path.exists(new_folder):
            os.makedirs(new_folder)
        shutil.move(os.path.join(source_folder, file), os.path.join(new_folder, file))

print("Splitting done successfully!")
