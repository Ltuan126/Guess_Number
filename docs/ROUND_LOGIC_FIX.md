# Round Logic Fix for Guess Number Game Server

## Problem Description

The server had several issues with round management that caused confusion:

1. **Round numbering started from 2 instead of 1**: When the first player joined, the round number was incorrectly incremented
2. **Subsequent players caused round skipping**: Each new player joining would trigger a new round, causing the round number to jump unexpectedly
3. **Incorrect result messages**: When a player guessed correctly, the message showed the wrong number (from the new round instead of the completed round)

## Root Causes

### 1. **Incorrect Round Initialization**
**File**: `server/server.py` - `on_join_room` function

**Before**:
```python
# Nếu đây là người chơi đầu tiên, reset vòng chơi
if len(room.players) == 1:
    game_manager._start_new_round(room)  # This caused round_number += 1
    logger.info(f"First player joined, started new round in room {room_id}")
```

**Problem**: 
- When creating a room, `round_number` is set to 1
- When the first player joins, `_start_new_round(room)` is called with `reset_mode=False`
- This causes `room.round_number += 1` → round 2 instead of round 1

### 2. **Round Number Increment Logic**
**File**: `server/server.py` - `_start_new_round` function

**Before**:
```python
def _start_new_round(self, room: Room, reset_mode: bool = False):
    """Bắt đầu vòng mới"""
    if reset_mode:
        room.round_number = 1
    else:
        room.round_number += 1  # This always incremented
```

**Problem**: 
- Even when starting the first round, the number was incremented
- This caused round numbers to be off by 1

### 3. **Result Message Timing Issue**
**File**: `server/server.py` - `make_guess` function

**Before**:
```python
# Tạo vòng mới
self._start_new_round(room)

return True, f"🎉 Chính xác! Số cần tìm là {room.current_round.number}", {
```

**Problem**: 
- `_start_new_round(room)` was called before returning the result
- This changed `room.current_round.number` to the new round's number
- The result message showed the wrong number

## Solutions Implemented

### 1. **Fixed Round Initialization**
**After**:
```python
# Nếu đây là người chơi đầu tiên, bắt đầu vòng 1
if len(room.players) == 1:
    # Không cần gọi _start_new_round vì phòng đã có vòng 1 sẵn
    logger.info(f"First player joined room {room_id}, room already has round 1 ready")
```

**Explanation**: 
- The room is created with `round_number = 1` and a ready `GameRound`
- No need to call `_start_new_round` when the first player joins
- The round is already ready to play

### 2. **Improved Round Number Logic**
**After**:
```python
def _start_new_round(self, room: Room, reset_mode: bool = False):
    """Bắt đầu vòng mới"""
    if reset_mode:
        room.round_number = 1
    elif room.round_number == 0:  # Nếu chưa có vòng nào
        room.round_number = 1
    else:
        room.round_number += 1
```

**Explanation**: 
- `reset_mode=True`: Forces round number to 1 (for room reset)
- `room.round_number == 0`: Handles edge case where no round exists
- Otherwise: Increments normally for new rounds

### 3. **Fixed Result Message**
**After**:
```python
# Lưu số đã đoán đúng trước khi tạo vòng mới
correct_number = room.current_round.number

# Tạo vòng mới
self._start_new_round(room)

return True, f"🎉 Chính xác! Số cần tìm là {correct_number}", {
```

**Explanation**: 
- Store the correct number before calling `_start_new_round`
- This ensures the result message shows the actual number that was guessed correctly
- The new round is created after the result is prepared

## Files Modified

1. **`server/server.py`**:
   - Fixed `on_join_room` function to not call `_start_new_round` unnecessarily
   - Improved `_start_new_round` function logic
   - Fixed `make_guess` function to preserve correct number in result message

2. **`client/test_rounds.html`**:
   - New test file specifically for testing round logic
   - Shows current round number, range, and end time
   - Helps verify that rounds are working correctly

## Expected Behavior After Fix

### **Before Fix**:
- Room created → Round 1
- First player joins → Round 2 (incorrect!)
- Second player joins → Round 3 (incorrect!)
- Correct guess message shows wrong number

### **After Fix**:
- Room created → Round 1 ✅
- First player joins → Round 1 (stays the same) ✅
- Second player joins → Round 1 (stays the same) ✅
- When someone guesses correctly → Round 2 ✅
- Correct guess message shows the right number ✅

## Testing

To test the fix:

1. **Start the server**: `python server/run_fixed.py`
2. **Open `client/test_rounds.html`** in a browser
3. **Create a room** and verify it starts at Round 1
4. **Join with first player** and verify Round 1 is maintained
5. **Join with second player** and verify Round 1 is still maintained
6. **Make a correct guess** and verify:
   - Message shows the correct number
   - Round advances to Round 2
   - New round information is displayed

## Benefits

1. **Correct Round Numbering**: Rounds now start from 1 and increment properly
2. **No More Round Skipping**: Players joining doesn't cause unexpected round changes
3. **Accurate Result Messages**: Correct guess messages show the right number
4. **Better User Experience**: Players can clearly see which round they're in
5. **Consistent Logic**: Round management follows expected behavior

## Notes

- **Room Creation**: Creates Round 1 immediately
- **First Player**: Joins existing Round 1 (no round change)
- **Subsequent Players**: Join existing Round 1 (no round change)
- **Correct Guess**: Advances to next round
- **Time Expiry**: Automatically advances to next round
- **Room Reset**: Forces Round 1 (admin function)
