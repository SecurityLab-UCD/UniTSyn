from transformers import AutoTokenizer, AutoModelForCausalLM,Trainer, TrainingArguments, AutoConfig
from datasets import load_dataset
import os
import torch
import torch.distributed as dist
#clean CUDA cache and define using cuda
torch.cuda.empty_cache()
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"

#define the gpu backend to launch training
dist.init_process_group(backend="nccl")

#train the models

#load the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-2B-multi")
model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-2B-multi")

# class CustomModel(AutoModelForCausalLM):
#     def __init__(self, config):
#         super().__init__(config)

#     def forward(self, input_ids, attention_mask, labels=None):
#         outputs = super().forward(input_ids=input_ids, attention_mask=attention_mask, labels=input_ids)
#         loss = outputs.loss
#         return loss

#     @classmethod
#     def from_pretrained(cls, pretrained_model_name_or_path, *model_args, **kwargs):
#         config = kwargs.pop('config', None)
#         if config is None:
#             config = AutoConfig.from_pretrained(pretrained_model_name_or_path, *model_args, **kwargs)
#         model = super().from_pretrained(pretrained_model_name_or_path, *model_args, config=config, **kwargs)
#         return model
    
# #use self-defined model inheriting from AutoModelForCausalLM
# model = CustomModel.from_pretrained("Salesforce/codegen-2B-multi")



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
    output_dir='./training/results',            
    num_train_epochs=3,                         
    per_device_train_batch_size=1,              # 每个设备的训练批量大小
    per_device_eval_batch_size=1,               # 每个设备的评估批量大小
    no_cuda=False,  
    warmup_steps=500,                           
    weight_decay=0.01,                          
    logging_dir='./logs',                       
    logging_steps=10,
    local_rank=-1
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=valid_dataset
)

trainer.train()

trainer.save_model("./training/saved_model")
results = trainer.evaluate(test_dataset)
