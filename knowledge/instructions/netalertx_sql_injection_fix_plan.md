# NetAlertX SQL Injection Vulnerability Fix - Implementation Plan

## Security Issues Identified

The NetAlertX reporting.py module has two critical SQL injection vulnerabilities:

1. **Lines 73-79**: `new_dev_condition` is directly concatenated into SQL query
2. **Lines 149-155**: `event_condition` is directly concatenated into SQL query

## Current Vulnerable Code Analysis

### Vulnerability 1 (Lines 73-79):
```python
new_dev_condition = get_setting_value('NTFPRCS_new_dev_condition').replace('{s-quote}',"'")
sqlQuery = f"""SELECT eve_MAC as MAC, eve_DateTime as Datetime, devLastIP as IP, eve_EventType as "Event Type", devName as "Device name", devComments as Comments  FROM Events_Devices
                WHERE eve_PendingAlertEmail = 1
                AND eve_EventType = 'New Device' {new_dev_condition} 
                ORDER BY eve_DateTime"""   
```

### Vulnerability 2 (Lines 149-155):
```python
event_condition = get_setting_value('NTFPRCS_event_condition').replace('{s-quote}',"'")
sqlQuery = f"""SELECT eve_MAC as MAC, eve_DateTime as Datetime, devLastIP as IP, eve_EventType as "Event Type", devName as "Device name", devComments as Comments  FROM Events_Devices
                WHERE eve_PendingAlertEmail = 1
                AND eve_EventType IN ('Connected', 'Down Reconnected', 'Disconnected','IP Changed') {event_condition} 
                ORDER BY eve_DateTime"""      
```

## Implementation Strategy

### 1. Create SafeConditionBuilder Class

Create `/server/db/sql_safe_builder.py` with:
- Whitelist of allowed filter conditions
- Parameter binding and sanitization
- Input validation methods
- Safe SQL snippet generation

### 2. Update reporting.py

Replace vulnerable string concatenation with:
- Parameterized queries
- Safe condition builder integration
- Robust input validation

### 3. Create Comprehensive Test Suite

Create `/test/test_sql_security.py` with:
- SQL injection attack tests
- Parameter binding validation
- Backward compatibility tests
- Performance impact tests

## Files to Modify/Create

1. **CREATE**: `/server/db/sql_safe_builder.py` - Safe SQL condition builder
2. **MODIFY**: `/server/messaging/reporting.py` - Replace vulnerable code
3. **CREATE**: `/test/test_sql_security.py` - Security test suite

## Implementation Steps

### Step 1: Create SafeConditionBuilder Class
- Define whitelist of allowed conditions and operators
- Implement parameter binding methods
- Add input validation and sanitization
- Create safe SQL snippet generation

### Step 2: Update reporting.py
- Import SafeConditionBuilder
- Replace direct string concatenation with safe builder calls
- Update get_notifications function with parameterized queries
- Maintain existing functionality while securing inputs

### Step 3: Create Test Suite
- Test various SQL injection payloads
- Validate parameter binding works correctly
- Ensure backward compatibility
- Performance regression tests

### Step 4: Integration Testing
- Run existing test suite
- Verify all functionality preserved
- Test edge cases and error conditions

## Security Requirements

1. **Zero SQL Injection Vulnerabilities**: All dynamic SQL must use parameterized queries
2. **Input Validation**: All user inputs must be validated and sanitized
3. **Whitelist Approach**: Only predefined, safe conditions allowed
4. **Parameter Binding**: No direct string concatenation in SQL queries
5. **Error Handling**: Graceful handling of invalid inputs

## Expected Outcome

- All SQL injection vulnerabilities eliminated
- Backward compatibility maintained
- Performance impact minimized
- Comprehensive test coverage
- Clean, maintainable code following security best practices