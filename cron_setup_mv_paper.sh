#!/bin/bash
# Crontab setup for Market Variation Paper Trading
# This file shows the cron entries you should add to your crontab
# Run: crontab -e and add these lines

# Market Variation Symbol Categorization (once daily at 5 AM)
0 5 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_symbols_mv.py >> /root/logs/mv_symbols.log 2>&1

# Market Variation Paper Trading (same schedule as regular breakout.py)
# Evening Check (9:30 PM)
30 21 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout:$(date +\%Y-\%m-\%d).log 2>&1

# Late Evening (10:45-11:45 PM)
45 22-23 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout:$(date +\%Y-\%m-\%d).log 2>&1

# Early Morning (12:45-3:45 AM next day)
45 0-3 * * 2-6 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout:$(date +\%Y-\%m-\%d).log 2>&1

# Optional: Check status at market open (9:31 AM)
31 9 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout:$(date +\%Y-\%m-\%d).log 2>&1

# Optional: Mid-day check (2 PM)
0 14 * * 1-5 /root/anaconda3/bin/python3 /root/breakout/breakout_mv_paper.py >> /root/logs/MV-Breakout:$(date +\%Y-\%m-\%d).log 2>&1
