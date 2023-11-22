"""
command to run the py file:
    torchrun --nproc_per_node=4  ./training/codegen_rust.py
"""

from transformers import AutoTokenizer, AutoModelForCausalLM,Trainer, TrainingArguments, AutoConfig
from datasets import load_dataset
import os
import torch
import torch.distributed as dist
import fire
import jsonlines

#clean CUDA cache and define using cuda
torch.cuda.empty_cache()

#define the gpu backend to launch training
dist.init_process_group(backend="nccl")

#watch the memory change
def print_memory_usage():
    print(f"Allocated memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
    print(f"Reserved memory:  {torch.cuda.memory_reserved() / 1024**3:.2f} GB")

#train the models

#load the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-2B-multi")
model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-2B-multi")

#stream loading data
processed_data_folder = './training/source'

#apply tokenizer
tokenizer.add_special_tokens({'pad_token': '[PAD]'})
def encode(examples):
    encoded = tokenizer(examples, truncation=True, padding='max_length', max_length=512, return_tensors='pt')
    encoded['labels'] = encoded['input_ids'].clone()
    return encoded

def load_data_in_batches(folder, batch_size):
    batch_data = []
    for filename in os.listdir(folder):
        if filename.endswith('success.jsonl'):
            file_path = os.path.join(folder, filename)
            with jsonlines.open(file_path) as reader:          
                for _, obj in enumerate(reader):
                    content = obj['test'] + "\n" + obj['code']
                    encoded = encode(content)
                    batch_data.append(encoded)
                    if len(batch_data) == batch_size:
                        yield batch_data
                        batch_data = []
            if batch_data:
                yield batch_data

def main():
    # Use yield to load data batch by batch
    for batch in load_data_in_batches(processed_data_folder, batch_size=8):
        training_args = TrainingArguments(
            output_dir='./training/results',            
            num_train_epochs=3,                         
            per_device_train_batch_size=1,              
            per_device_eval_batch_size=1,               
            no_cuda=False,  
            warmup_steps=500,                           
            weight_decay=0.01,                          
            logging_dir='./logs',                       
            logging_steps=10,
            local_rank=-1,
            max_steps=10000
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=batch,
            # eval_dataset=valid_dataset
        )

        trainer.train()

        #clean cache every batch
        torch.cuda.empty_cache()
        trainer.save_model("./training/saved_model")
        print_memory_usage()
    # results = trainer.evaluate(test_dataset)

if __name__ == "__main__":
    fire.Fire(main)

#define in function style and change it to main ✅
#using lora to solve bugs?
#writing train method in conflunence
