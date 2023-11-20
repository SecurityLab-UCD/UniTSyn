from transformers import AutoTokenizer, AutoModelForCausalLM,Trainer, TrainingArguments
from datasets import load_dataset
import os

#define using cuda
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3,4,5,6"


#train the model

#load the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-2B-multi")
model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-2B-multi")

train_dataset = load_dataset('text', data_files='./training/data/train_dataset.txt')['train']
valid_dataset = load_dataset('text', data_files='./training/data/valid_dataset.txt')['train']
test_dataset = load_dataset('text', data_files='./training/data/test_dataset.txt')['train']


#apply tokenizer
tokenizer.add_special_tokens({'pad_token': '[PAD]'})
def encode(examples):
    return tokenizer(examples['text'], truncation=True, padding='max_length', max_length=512)

train_dataset = train_dataset.map(encode, batched=True)
valid_dataset = valid_dataset.map(encode, batched=True)
test_dataset = test_dataset.map(encode, batched=True)

train_dataset.set_format('torch', columns=['input_ids', 'attention_mask'])
valid_dataset.set_format('torch', columns=['input_ids', 'attention_mask'])
test_dataset.set_format('torch', columns=['input_ids', 'attention_mask'])

training_args = TrainingArguments(
    output_dir='./training/results',          # 输出目录
    num_train_epochs=3,              # 训练轮数
    per_device_train_batch_size=1,   # 每个设备的训练批量大小
    per_device_eval_batch_size=1,    # 每个设备的评估批量大小
    no_cuda=False,
    warmup_steps=500,                # 预热步骤
    weight_decay=0.01,               # 权重衰减
    logging_dir='./logs',            # 日志目录
    logging_steps=10,
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
