import os
import jsonlines
from sklearn.model_selection import train_test_split

# Define the size of each small file
batch_size = 100 

# Load the dataset
source_codes = []
folder_path = './training/source'

def save_data(data, filename):
    with open(filename, 'w') as file:
        for item in data:
            file.write(item + '\n')

file_number = 1

for filename in os.listdir(folder_path):
    if filename.endswith('.jsonl'):
        file_path = os.path.join(folder_path, filename)

        with jsonlines.open(file_path) as reader:
            for obj in reader:
                # Process each JSON object
                source_code = obj.get('test', '')
                if source_code:
                    source_codes.append(source_code)
                    if len(source_codes) >= batch_size:
                        # Save data in batches
                        train_data, temp_data = train_test_split(source_codes, test_size=0.3, random_state=42)
                        valid_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)

                        train_filename = f'./training/batch_data/train_dataset{file_number}.txt'
                        valid_filename = f'./training/batch_data/valid_dataset{file_number}.txt'
                        test_filename = f'./training/batch_data/test_dataset{file_number}.txt'

                        save_data(train_data, train_filename)
                        save_data(valid_data, valid_filename)
                        save_data(test_data, test_filename)

                        # Reset source_codes
                        source_codes = []

                        file_number += 1

# Save the remaining data
if source_codes:
    train_data, temp_data = train_test_split(source_codes, test_size=0.3, random_state=42)
    valid_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)

    train_filename = f'./training/batch_data/train_dataset{file_number}.txt'
    valid_filename = f'./training/batch_data/valid_dataset{file_number}.txt'
    test_filename = f'./training/batch_data/test_dataset{file_number}.txt'

    save_data(train_data, train_filename)
    save_data(valid_data, valid_filename)
    save_data(test_data, test_filename)
