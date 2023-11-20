import os
import jsonlines
from sklearn.model_selection import train_test_split

#load datasets

source_codes = []
folder_path = './training/source'


for filename in os.listdir(folder_path):
    if filename.endswith('.jsonl'):
        file_path = os.path.join(folder_path, filename)

        with jsonlines.open(file_path) as reader:
            for obj in reader:
                # 处理每个 JSON 对象
                source_code = obj.get('test','')
                if source_code:
                    source_codes.append(source_code)



# divided the datasets
train_data, temp_data = train_test_split(source_codes, test_size=0.3, random_state=42)
valid_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)

#save data
def save_data(data, filename):
    with open(filename, 'w') as file:
        for item in data:
            file.write(item + '\n')

save_data(train_data, './training/data/train_dataset.txt')
save_data(valid_data, './training/data/valid_dataset.txt')
save_data(test_data, './training/data/test_dataset.txt')
