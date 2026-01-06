# Q6 Feedback Missing - Root Cause Analysis

## Problem
Q6 (the final behavioral question) does not receive feedback before the interview ends and the final report is generated.

## Current Flow

### Question Count = 6 (Q6 is ASKED)
**Location:** `api/index.py` lines 476-485
```python
elif question_count == 6:
    messages.append({
        "role": "user",
        "content": (
            f"User Answer: {message}. \n"
            "Step 1: Provide brief, constructive feedback. (Put ONLY this critique in 'feedback' field).\n"
            "Step 2: Generate closing transition: 'The final question I have for you is...' (Put in 'next_question' field).\n"
            "Step 3: Ask the final behavioral question. (Append to 'next_question' field)."
        )
    })
```

**What happens:** User answers Q5, AI provides feedback + asks Q6

### Question Count = 7 (Q6 is ANSWERED, but...)
**Location:** `api/index.py` line 487
```python
elif question_count > 6:
    # FINAL REPORT LOGIC
```

**What happens:** User answers Q6, but instead of getting feedback, the system **immediately jumps to final report generation** because `question_count = 7` triggers `question_count > 6`.

## Root Cause

**The problem is a logic gap:**

1. When `question_count = 6`, the AI asks Q6
2. When `question_count = 7` (user just answered Q6), the code skips the feedback step and goes straight to final report generation
3. **There's no feedback cycle for Q6's answer!**

## The Flow Should Be

```
count=1: Initial greeting
count=2: Ask Q1 (background)
count=3: Feedback for Q1 + Ask Q2
count=4: Feedback for Q2 + Ask Q3
count=5: Feedback for Q3 + Ask Q4
count=6: Feedback for Q4 + Ask Q5
count=7: Feedback for Q5 + Ask Q6  ← Currently does this
count=8: Feedback for Q6 + Generate Final Report  ← Currently SKIPS this!
```

But the current code does:
```
count=7: Feedback for Q5 + Ask Q6
count=8: SKIP FEEDBACK, Generate Final Report immediately
```

Wait, let me re-check. The issue might be different...

Actually, looking more carefully:

- `question_count == 6` means we're processing Q5's answer (6th turn), so we give feedback on Q5 and ask Q6
- `question_count > 6` (i.e., count=7) means we're processing Q6's answer, and we jump straight to final report

## Solutions

### Option 1: Add Q6 Feedback Step (Recommended)
Add a new condition for `question_count == 7` that provides feedback on Q6 BEFORE generating the final report:

```python
elif question_count == 7:
    messages.append({
        "role": "user",
        "content": (
            f"User Answer: {message}. \n"
            "Step 1: Provide brief, constructive feedback on this final answer. (Put in 'feedback' field).\n"
            "Step 2: Generate a brief closing statement. (Put in 'next_question' field).\n"
        )
    })

elif question_count > 7:
    # FINAL REPORT LOGIC
```

Then update the final report trigger to `question_count > 7`.

### Option 2: Include Q6 Feedback in Final Report
Modify the final report generation to include Q6's feedback as part of the report introduction.

## Recommended Fix

**Option 1** is cleaner and maintains consistency - every question should get feedback before the final report is shown.

## Impact
- Users don't receive immediate feedback on their final answer
- Q6 feels incomplete without acknowledgment
- The interview ends abruptly after Q6 answer
