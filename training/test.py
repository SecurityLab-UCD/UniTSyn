import torch
print(torch.cuda.is_available())  # 应该返回 True
print(torch.cuda.device_count())  # 显示可用的 GPU 数量
print(torch.cuda.get_device_name(0))  # 显示第一个 GPU 的名称