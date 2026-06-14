import os
import torch

def find_nvidia_cuda_device():
    """Return the first CUDA device index whose name contains 'NVIDIA', or None."""
    if not torch.cuda.is_available():
        return None
    for i in range(torch.cuda.device_count()):
        try:
            name = torch.cuda.get_device_properties(i).name
        except Exception:
            name = None
        if name and "NVIDIA" in name.upper():
            return i
    return 0 if torch.cuda.device_count() > 0 else None

def pin_process_to_cuda(device_index: int):
    """Pin the current process to a specific CUDA device.

    This sets CUDA_VISIBLE_DEVICES and calls torch.cuda.set_device.
    """
    if device_index is None:
        return
    os.environ["CUDA_VISIBLE_DEVICES"] = str(device_index)
    try:
        # After setting CUDA_VISIBLE_DEVICES we set torch device 0 which maps
        # to the selected visible device.
        torch.cuda.set_device(0)
    except Exception:
        pass
