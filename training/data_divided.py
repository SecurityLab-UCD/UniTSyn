import os
import jsonlines
# from sklearn.model_selection import train_test_split

#load datasets

source_codes = []
source_folder = './training/source'
output_folder = './training/data'

for filename in os.listdir(source_folder):
    if filename.endswith('success.jsonl'):
        file_path = os.path.join(source_folder, filename)
        with jsonlines.open(file_path) as reader:
            for i,obj in enumerate(reader):
                output_file = os.path.join(output_folder, f"{os.path.basename(file_path)}_{i}.txt")
                with open(output_file, 'w') as f:
                    f.write(obj['code'] + "\n" + obj['test'])



# # divided the datasets
# train_data, temp_data = train_test_split(source_codes, test_size=0.3, random_state=42)
# valid_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)

# #save data
# def save_data(data, filename):
#     with open(filename, 'w') as file:
#         for item in data:
#             file.write(item + '\n')

# save_data(train_data, './training/data/train_dataset.txt')
# save_data(valid_data, './training/data/valid_dataset.txt')
# save_data(test_data, './training/data/test_dataset.txt')
