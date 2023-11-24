import os
os.environ["CUDA_VISIBLE_DEVICES"]="0"
import torch
import torch.nn as nn
import bitsandbytes as bnb
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, AutoConfig
from datasets import load_dataset
from peft import LoraConfig, get_peft_model

torch.cuda.empty_cache()

model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-2B-multi")
tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-2B-multi")


for param in model.parameters():
  param.requires_grad = False  # freeze the model - train adapters later
  if param.ndim == 1:
    # cast the small parameters (e.g. layernorm) to fp32 for stability
    param.data = param.data.to(torch.float32)

model.gradient_checkpointing_enable()  # reduce number of stored activations
model.enable_input_require_grads()

config = LoraConfig(
    r=16, #attention heads
    lora_alpha=32, #alpha scaling
    # target_modules=["q_proj", "v_proj"], #if you know the 
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, config)


train_dataset = load_dataset('text', data_files='./training/data/train_dataset.txt')['train']
valid_dataset = load_dataset('text', data_files='./training/data/valid_dataset.txt')['train']
test_dataset = load_dataset('text', data_files='./training/data/test_dataset.txt')['train']


#apply tokenizer
tokenizer.add_special_tokens({'pad_token': '[PAD]'})
def encode(examples):
    encoded = tokenizer(examples['text'], truncation=True, padding='max_length', max_length=256, return_tensors='pt')
    encoded['labels'] = encoded['input_ids'].clone()
    return encoded


train_dataset = train_dataset.map(encode, batched=True)
valid_dataset = valid_dataset.map(encode, batched=True)
test_dataset = test_dataset.map(encode, batched=True)

train_dataset.set_format('torch', columns=['input_ids', 'attention_mask', 'labels'])
valid_dataset.set_format('torch', columns=['input_ids', 'attention_mask', 'labels'])
test_dataset.set_format('torch', columns=['input_ids', 'attention_mask', 'labels'])

training_args = TrainingArguments(
    output_dir='./results',            
    num_train_epochs=3,                         
    per_device_train_batch_size=1,              # 每个设备的训练批量大小
    per_device_eval_batch_size=1,               # 每个设备的评估批量大小
    no_cuda=False,  
    warmup_steps=500,                           
    weight_decay=0.01,                          
    logging_dir='./logs',                       
    logging_steps=10,
    local_rank=-1,
    fp16=True
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=valid_dataset
)

trainer.train()

trainer.save_model("./training/saved_model")