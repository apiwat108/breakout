# Complete Crontab Setup for MV System
# ======================================

## Current Setup Analysis

### Your Existing Breakout.py (Real Account)
```
30 21 * * 1-5 python /root/breakout/breakout.py >> /root/Breakout:2026-02-18.log 2>&1
45 22-23 * * 1-5 python /root/breakout/breakout.py >> /root/Breakout:2026-02-18.log 2>&1
45 0-3 * * 2-6 python /root/breakout/breakout.py >> /root/Breakout:2025-Feb-20B.log 2>&1
```

## NEW: Market Variation System

### 1. Daily Symbol Categorization (Once per day)
```bash
# Run at 5:00 AM EST before market opens
0 5 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_symbols_mv.py >> /root/logs/mv_symbols.log 2>&1
```

**What it does:**
- Analyzes all symbols in your watchlist
- Categorizes them (keeping_up, turning_down, etc.)
- Updates mv_daily_statistics table
- Provides data for web dashboard

### 2. MV Paper Trading (Same schedule as breakout.py)
```bash
# Evening Check - 9:30 PM EST
30 21 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout-$(date +\%F).log 2>&1

# Late Evening - 10:45-11:45 PM EST  
45 22-23 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout-$(date +\%F).log 2>&1

# Early Morning - 12:45-3:45 AM EST (next day)
45 0-3 * * 2-6 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout-$(date +\%F).log 2>&1
```

**What it does:**
- Uses Paper Account 1 from config_mv_paper.py
- Trades symbols based on MV categorization
- Adjusts position sizing based on market conditions
- Checks breakout_metadata for special symbols
- Logs to separate MV-Breakout log files

## How to Add to Your Crontab

1. SSH into your Linode server
2. Run: `crontab -e`
3. Add the NEW lines above (keep your existing breakout.py lines)
4. Save and exit

## Complete Crontab Example
```bash
# Original Breakout System (Real Account)
30 21 * * 1-5 python /root/breakout/breakout.py >> /root/Breakout:2026-02-18.log 2>&1
45 22-23 * * 1-5 python /root/breakout/breakout.py >> /root/Breakout:2026-02-18.log 2>&1  
45 0-3 * * 2-6 python /root/breakout/breakout.py >> /root/Breakout:2025-Feb-20B.log 2>&1

# Market Variation System
0 5 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_symbols_mv.py >> /root/logs/mv_symbols.log 2>&1
30 21 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout-$(date +\%F).log 2>&1
45 22-23 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout-$(date +\%F).log 2>&1
45 0-3 * * 2-6 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout-$(date +\%F).log 2>&1
```

## Key Differences

| Feature | breakout.py | breakout_mv_paper.py |
|---------|-------------|----------------------|
| Account | Real Account | Paper Account 1 |
| Config | config.py | config_mv_paper.py |
| Database | app.db | app_mv |
| Position Sizing | Fixed | Market Variation Adjusted |
| Symbol Selection | Static list | MV categorization |
| Logs | /root/Breakout:*.log | /root/logs/MV-Breakout-*.log |

## Monitoring

### Check if running:
```bash
ps aux | grep breakout
```

### View logs:
```bash
# Regular breakout
tail -f /root/Breakout:2026-02-18.log

# MV categorization
tail -f /root/logs/mv_symbols.log

# MV paper trading
tail -f /root/logs/MV-Breakout-$(date +%F).log
```

### Check crontab:
```bash
crontab -l
```

## Notes

1. **Both systems run in parallel** - Your original breakout.py continues with real account
2. **MV system is paper only** - Safe testing of the new strategy
3. **Logs are separate** - Easy to compare performance
4. **Databases are separate** - No interference between systems
