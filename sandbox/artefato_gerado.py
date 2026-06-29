import psutil
import time

def get_memory_usage():
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "percent": memory.percent,
        "used": memory.used,
        "free": memory.free,
        "active": memory.active,
        "inactive": memory.inactive,
        "buffers": memory.buffers,
        "cached": memory.cached
    }

def print_memory_usage():
    while True:
        mem_info = get_memory_usage()
        print(f"Total Memory: {mem_info['total'] / (1024 ** 3):.2f} GB")
        print(f"Available Memory: {mem_info['available'] / (1024 ** 3):.2f} GB")
        print(f"Used Memory: {mem_info['used'] / (1024 ** 3):.2f} GB")
        print(f"Memory Usage Percentage: {mem_info['percent']}%")
        print("-" * 40)
        time.sleep(5)

if __name__ == "__main__":
    print_memory_usage()