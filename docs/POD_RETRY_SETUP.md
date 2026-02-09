# POD Auto-Retry System - Setup Guide

## Overview

The POD Auto-Retry System automatically retries failed POD fetches with intelligent backoff scheduling and error handling.

## Components

### 1. `pod_fetch_worker.py` (Existing)

- **Purpose**: Process NEW claims with `pending` POD status
- **Schedule**: Every 30 minutes
- **Handles**: Initial POD fetches for newly created claims

### 2. `pod_retry_scheduler.py` (New)

- **Purpose**: Retry FAILED POD fetches with exponential backoff
- **Schedule**: Every hour
- **Handles**: Claims with `failed` POD status

## Retry Strategy

The retry scheduler uses **exponential backoff** to avoid overwhelming APIs:

| Attempt | Wait Time | Total Time Since Failure |
|---------|-----------|--------------------------|
| 1       | 1 hour    | 1 hour                   |
| 2       | 6 hours   | 7 hours                  |
| 3       | 24 hours  | 31 hours (~1.3 days)     |
| 4       | 72 hours  | 103 hours (~4.3 days)    |

After 4 failed attempts with persistent errors, the system:

- Stops retrying
- Sends email notification to the client (persistent errors only)
- Logs final failure

## Smart Features

### 1. Error Classification

- **Persistent Errors**: User action required (e.g., "Invalid tracking number")
  - Sends email notification after max retries
  - Skips further automatic retries
  
- **Temporary Errors**: Auto-retry (e.g., "API timeout", "Rate limit")
  - Continues retrying with backoff
  - No email until max retries reached

### 2. Rate Limit Awareness

- Respects carrier API limits (e.g., 100/day for Chronopost)
- Automatically skips carriers at limit
- Resumes next day when limits reset

### 3. Comprehensive Logging

- All runs logged to `logs/pod_retry_scheduler.log`
- Detailed stats: success/failed/skipped counts
- API usage monitoring
- Duration tracking

## Setup Instructions

### Windows (Task Scheduler)

#### Initial Setup

```powershell
# Navigate to project directory
cd D:\Recours_Ecommerce

# Test the scheduler manually
python scripts\pod_retry_scheduler.py

# Create scheduled task (run hourly)
schtasks /create ^
  /tn "PODRetryScheduler" ^
  /tr "python D:\Recours_Ecommerce\scripts\pod_retry_scheduler.py" ^
  /sc hourly ^
  /mo 1 ^
  /st 00:00
```

#### Verify Task

```powershell
# List scheduled tasks
schtasks /query /tn "PODRetryScheduler" /fo LIST /v

# Run task manually
schtasks /run /tn "PODRetryScheduler"

# View logs
type logs\pod_retry_scheduler.log
```

#### Modify Schedule

```powershell
# Change to run every 2 hours
schtasks /change /tn "PODRetryScheduler" /sc hourly /mo 2

# Disable temporarily
schtasks /change /tn "PODRetryScheduler" /disable

# Enable again
schtasks /change /tn "PODRetryScheduler" /enable

# Delete task
schtasks /delete /tn "PODRetryScheduler" /f
```

### Linux (Crontab)

#### Initial Setup

```bash
# Navigate to project directory
cd /path/to/Recours_Ecommerce

# Test the scheduler manually
python3 scripts/pod_retry_scheduler.py

# Edit crontab
crontab -e

# Add this line (runs every hour at :00)
0 * * * * cd /path/to/Recours_Ecommerce && python3 scripts/pod_retry_scheduler.py >> logs/cron.log 2>&1
```

#### Verify Cron

```bash
# List cron jobs
crontab -l

# View logs
tail -f logs/pod_retry_scheduler.log
tail -f logs/cron.log
```

## Configuration

### Batch Size

Controls how many claims to process per run:

```bash
# Default: 30 claims per run
python scripts/pod_retry_scheduler.py --batch-size 30

# Process more claims (use if backlog builds up)
python scripts/pod_retry_scheduler.py --batch-size 50
```

### Max Retries

Controls maximum retry attempts:

```bash
# Default: 4 attempts
python scripts/pod_retry_scheduler.py --max-retries 4

# More persistent (6 attempts)
python scripts/pod_retry_scheduler.py --max-retries 6
```

### Schedule via Task Scheduler with Args

```powershell
schtasks /create ^
  /tn "PODRetryScheduler" ^
  /tr "python D:\Recours_Ecommerce\scripts\pod_retry_scheduler.py --batch-size 50 --max-retries 5" ^
  /sc hourly ^
  /mo 1
```

## Monitoring

### Check Logs

```bash
# Windows
type logs\pod_retry_scheduler.log | more

# Linux
tail -100 logs/pod_retry_scheduler.log
```

### Log Format

```
2026-02-06 14:00:00 - [INFO] - __main__ - ======================================================================
2026-02-06 14:00:00 - [INFO] - __main__ - POD AUTO-RETRY SCHEDULER - Starting
2026-02-06 14:00:00 - [INFO] - __main__ - Batch size: 30 | Max retries: 4
2026-02-06 14:00:00 - [INFO] - __main__ - ======================================================================
2026-02-06 14:00:01 - [INFO] - __main__ - Found 5 claim(s) to retry
2026-02-06 14:00:01 - [INFO] - __main__ - [1] Retry #2 for CLM-2024-001 (Chronopost)
2026-02-06 14:00:02 - [INFO] - __main__ - ✅ SUCCESS: POD fetched for CLM-2024-001 after 2 attempts
...
2026-02-06 14:00:10 - [INFO] - __main__ - Duration: 9.45s
2026-02-06 14:00:10 - [INFO] - __main__ - Total processed: 5
2026-02-06 14:00:10 - [INFO] - __main__ - ✅ Success: 3
2026-02-06 14:00:10 - [INFO] - __main__ - ❌ Failed: 2
2026-02-06 14:00:10 - [INFO] - __main__ - Success rate: 60.0%
```

### Success Metrics

Monitor these metrics in logs:

- **Success rate**: Should improve over time as temporary errors resolve
- **Skipped (persistent)**: Claims with errors requiring manual intervention
- **Skipped (rate limit)**: Indicates API limits reached
- **Max retries reached**: Claims that exhausted all retry attempts

## Database Schema

The scheduler adds tracking columns to the `claims` table:

```sql
ALTER TABLE claims ADD COLUMN pod_retry_count INTEGER DEFAULT 0;
ALTER TABLE claims ADD COLUMN pod_last_retry_at TIMESTAMP;
```

These columns are automatically added on first run if missing.

## Troubleshooting

### Issue: "No failed PODs eligible for retry"

**Solution**: This is normal if no PODs have failed recently. Check:

```sql
SELECT COUNT(*) FROM claims WHERE pod_fetch_status = 'failed';
```

### Issue: High "Skipped (rate limit)" count

**Solution**:

- Reduce batch size: `--batch-size 20`
- Carrier API limits reached, will reset tomorrow
- Check API usage in logs

### Issue: All retries fail

**Solution**:

1. Check carrier API credentials in `.streamlit/secrets.toml`
2. Verify network connectivity
3. Review error messages in logs
4. Test manual POD fetch in UI

### Issue: Notifications not sending

**Solution**:

1. Check email settings in database
2. Verify SMTP configuration
3. Review `logs/email_sender.log`
4. Ensure NotificationManager preferences are set

## Best Practices

1. **Monitor logs weekly** to catch recurring issues
2. **Set up log rotation** to prevent logs from growing too large
3. **Test manually** after making changes:

   ```bash
   python scripts/pod_retry_scheduler.py --batch-size 5
   ```

4. **Back up database** before modifying retry logic
5. **Review API usage** to avoid hitting carrier limits

## Performance Tips

- **Optimal schedule**: Hourly runs handle most failures efficiently
- **Batch size**: 30-50 is optimal for most workloads
- **Max retries**: 4 attempts balances persistence vs. API usage
- **Night runs**: Consider reducing frequency at night (3AM-6AM) when claims are low

## Integration with Existing Workers

### Complete POD Workflow

1. **New Claim Created** → `pod_fetch_status = 'pending'`
2. **pod_fetch_worker.py** (every 30 min) → Attempts initial fetch
3. **If Success** → `pod_fetch_status = 'success'`, POD URL stored
4. **If Failure** → `pod_fetch_status = 'failed'`, error logged
5. **pod_retry_scheduler.py** (every hour) → Retries with backoff
6. **After 4 Attempts** → Sends notification, stops retrying

### Worker Coordination

- Both workers use same `APIRequestQueue` for rate limiting
- No conflicts - `fetch_worker` handles 'pending', `retry_scheduler` handles 'failed'
- Can run simultaneously without issues

## Support

For issues or questions:

1. Check logs first: `logs/pod_retry_scheduler.log`
2. Review this documentation
3. Test manually with small batch size
4. Contact: <admin@refundly.ai>
