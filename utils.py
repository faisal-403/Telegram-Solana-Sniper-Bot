import re
from datetime import datetime

def validate_token_address(address: str) -> bool:
    return len(address) == 44 and address.isalnum()

def format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def shorten_address(address: str, chars: int = 6) -> str:
    return f"{address[:chars]}...{address[-chars:]}"