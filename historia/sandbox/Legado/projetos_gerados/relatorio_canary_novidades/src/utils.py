# utils.py

import random
import string

def generate_random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def is_valid_integer(value):
    """Check if the value can be converted to an integer."""
    try:
        int(value)
        return True
    except ValueError:
        return False

def clamp(value, min_value, max_value):
    """Clamp a value between a minimum and maximum value."""
    return max(min_value, min(max_value, value))

# Example usage of the functions
if __name__ == "__main__":
    print(generate_random_string(8))
    print(is_valid_integer("123"))
    print(clamp(5, 0, 10))