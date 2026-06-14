"""Early initialization to pin process to NVIDIA CUDA device.

Import this module at the very top of service entrypoints to ensure
the process is bound to the discrete NVIDIA GPU before heavy ML
libraries are imported.
"""
try:
    # Import lazily and guard in case `torch` or gpu utilities aren't installed
    # in lightweight services (some containers don't include ML deps).
    from . import gpu_utils

    device = None
    try:
        device = gpu_utils.find_nvidia_cuda_device()
    except Exception:
        device = None

    if device is not None:
        try:
            gpu_utils.pin_process_to_cuda(device)
            print(f"[early_init] Pinned process to CUDA device {device}")
        except Exception:
            # Don't raise during early init; log and continue.
            print("[early_init] Failed to pin process to CUDA device")
    else:
        print("[early_init] No NVIDIA CUDA device found or gpu_utils unavailable")
except Exception:
    # If import fails (e.g. no torch installed), skip early init silently.
    print("[early_init] Skipping GPU pinning (gpu_utils not available)")
