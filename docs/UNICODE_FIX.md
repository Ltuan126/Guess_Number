# Unicode Encoding Fix for Guess Number Game Server

## Problem Description

The server was encountering Unicode encoding errors when trying to log Vietnamese characters (like "Thách Đấu") to log files. The error occurred because:

1. **Default Encoding Issue**: On Windows, the default encoding for file operations is `cp1258` (Vietnamese), which cannot handle all Unicode characters properly.
2. **Logging Configuration**: The `logging.FileHandler` was not specifying an encoding, causing it to use the system default.
3. **Character Validation**: The room ID validation was too restrictive and didn't allow Vietnamese characters.

## Error Messages

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u1ea5' in position 137: character maps to <undefined>
```

This error occurred when trying to log messages containing Vietnamese characters like "Thách Đấu".

## Solutions Implemented

### 1. Fixed Logging Configuration

**File**: `server/server.py` and `server/start_server.py`

**Before**:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),  # No encoding specified
        logging.StreamHandler()
    ]
)
```

**After**:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),  # UTF-8 encoding specified
        logging.StreamHandler()
    ]
)
```

### 2. Improved Character Validation

**File**: `server/server.py`

**Before**: Strict alphanumeric validation that rejected Vietnamese characters
```python
if not room_id.replace('_', '').replace('-', '').isalnum():
    logger.warning(f"Create room failed: Invalid characters in room_id: {room_id}")
    return None
```

**After**: More flexible validation using Unicode character categories
```python
import unicodedata
allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ -')
for char in room_id:
    if char not in allowed_chars and not unicodedata.category(char).startswith('L'):
        logger.warning(f"Create room failed: Invalid characters in room_id: {room_id}")
        return None
```

**Explanation**: 
- `unicodedata.category(char).startswith('L')` allows any Unicode letter (including Vietnamese characters)
- `allowed_chars` includes basic alphanumeric characters, spaces, underscores, and hyphens
- This approach is more maintainable and follows Unicode standards

### 3. Updated Player Name Validation

Similar improvements were made to player name validation to allow Vietnamese characters.

## Files Modified

1. `server/server.py` - Main server file with logging and validation fixes
2. `server/start_server.py` - Startup script with logging configuration
3. `client/test.html` - Added helpful notes about character restrictions
4. `client/test_unicode.html` - New test file for Unicode functionality

## Testing

To test the fix:

1. **Start the server**: `python server/run_fixed.py`
2. **Open test_unicode.html** in a browser
3. **Try creating a room** with Vietnamese characters like "Thách Đấu"
4. **Check the logs** - they should now handle Vietnamese characters without errors

## Benefits

1. **No More Encoding Errors**: Vietnamese and other Unicode characters are properly handled
2. **Better User Experience**: Users can use their native language in room names
3. **Maintainable Code**: Unicode validation follows Python standards
4. **Cross-Platform Compatibility**: UTF-8 encoding works consistently across different operating systems

## Notes

- **Room ID**: Still has some restrictions for security and URL compatibility
- **Room Name**: Fully supports Vietnamese and other Unicode characters
- **Player Names**: Support Vietnamese characters
- **Logs**: All log files now use UTF-8 encoding

## Future Improvements

1. Consider allowing more special characters in room IDs while maintaining security
2. Add input sanitization to prevent potential injection attacks
3. Consider adding language-specific validation rules
4. Add tests for Unicode edge cases
