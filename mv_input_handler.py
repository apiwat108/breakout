"""
Market Variation Input Handler
================================
This module handles manual input of breakout metadata including:
- Breakout date for each symbol
- Stop loss price from graph analysis
- Optional notes about the setup

Usage:
    python mv_input_handler.py
    
    Or import as module:
    from mv_input_handler import add_breakout_metadata, get_breakout_metadata
"""

import psycopg2
import psycopg2.extras
import config
from datetime import datetime


class BreakoutInputHandler:
    """Handle manual input of breakout metadata for symbols"""
    
    def __init__(self):
        self.connection = psycopg2.connect(
            host=config.DB_HOST,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create necessary tables if they don't exist"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mv_breakout_metadata (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                breakout_date DATE NOT NULL,
                stop_loss_price NUMERIC NOT NULL,
                entry_price NUMERIC,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(symbol, breakout_date)
            )
        """)
        self.connection.commit()
    
    def add_breakout_metadata(self, symbol, breakout_date, stop_loss_price, 
                             entry_price=None, notes=None):
        """
        Add or update breakout metadata for a symbol
        
        Args:
            symbol (str): Stock symbol
            breakout_date (str or datetime): Date of breakout (YYYY-MM-DD)
            stop_loss_price (float): Stop loss price from graph analysis
            entry_price (float, optional): Entry price if known
            notes (str, optional): Additional notes about the setup
            
        Returns:
            int: ID of the inserted/updated record
        """
        if isinstance(breakout_date, str):
            breakout_date = datetime.strptime(breakout_date, '%Y-%m-%d').date()
        
        try:
            # Try to insert, update if exists
            self.cursor.execute("""
                INSERT INTO mv_breakout_metadata 
                    (symbol, breakout_date, stop_loss_price, entry_price, notes, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (symbol, breakout_date) 
                DO UPDATE SET 
                    stop_loss_price = EXCLUDED.stop_loss_price,
                    entry_price = EXCLUDED.entry_price,
                    notes = EXCLUDED.notes,
                    updated_at = CURRENT_TIMESTAMP,
                    is_active = TRUE
                RETURNING id
            """, (symbol, breakout_date, stop_loss_price, entry_price, notes))
            
            record_id = self.cursor.fetchone()['id']
            self.connection.commit()
            print(f"✓ Added/Updated breakout metadata for {symbol}")
            return record_id
            
        except Exception as e:
            self.connection.rollback()
            print(f"✗ Error adding metadata for {symbol}: {e}")
            raise
    
    def add_batch_metadata(self, metadata_list):
        """
        Add multiple breakout metadata entries at once
        
        Args:
            metadata_list (list): List of dicts with keys:
                - symbol (str)
                - breakout_date (str or datetime)
                - stop_loss_price (float)
                - entry_price (float, optional)
                - notes (str, optional)
                
        Returns:
            tuple: (successful_count, failed_count, failed_symbols)
        """
        successful = 0
        failed = 0
        failed_symbols = []
        
        for metadata in metadata_list:
            try:
                self.add_breakout_metadata(
                    symbol=metadata['symbol'],
                    breakout_date=metadata['breakout_date'],
                    stop_loss_price=metadata['stop_loss_price'],
                    entry_price=metadata.get('entry_price'),
                    notes=metadata.get('notes')
                )
                successful += 1
            except Exception as e:
                failed += 1
                failed_symbols.append(metadata['symbol'])
                print(f"Failed to add {metadata['symbol']}: {e}")
        
        return successful, failed, failed_symbols
    
    def get_breakout_metadata(self, symbol=None, active_only=True):
        """
        Retrieve breakout metadata
        
        Args:
            symbol (str, optional): Specific symbol to retrieve, or None for all
            active_only (bool): Only return active breakouts
            
        Returns:
            list: List of breakout metadata records
        """
        query = "SELECT * FROM mv_breakout_metadata WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = %s"
            params.append(symbol)
        
        if active_only:
            query += " AND is_active = TRUE"
        
        query += " ORDER BY breakout_date DESC, symbol"
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def deactivate_symbol(self, symbol, breakout_date=None):
        """
        Deactivate a symbol (e.g., when position is closed or strategy no longer applies)
        
        Args:
            symbol (str): Stock symbol
            breakout_date (str or datetime, optional): Specific breakout date, or None for all
        """
        query = "UPDATE mv_breakout_metadata SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE symbol = %s"
        params = [symbol]
        
        if breakout_date:
            if isinstance(breakout_date, str):
                breakout_date = datetime.strptime(breakout_date, '%Y-%m-%d').date()
            query += " AND breakout_date = %s"
            params.append(breakout_date)
        
        self.cursor.execute(query, params)
        self.connection.commit()
        print(f"✓ Deactivated {symbol}")
    
    def get_active_symbols(self):
        """Get list of all currently active symbols"""
        self.cursor.execute("""
            SELECT DISTINCT symbol 
            FROM mv_breakout_metadata 
            WHERE is_active = TRUE
            ORDER BY symbol
        """)
        return [row['symbol'] for row in self.cursor.fetchall()]
    
    def interactive_input(self):
        """Interactive command-line interface for adding breakout metadata"""
        print("\n" + "="*60)
        print("Market Variation - Breakout Metadata Input")
        print("="*60)
        print("\nEnter breakout metadata from your graph analysis")
        print("(Press Ctrl+C to exit)\n")
        
        try:
            while True:
                print("-" * 60)
                symbol = input("Symbol (e.g., AAPL): ").strip().upper()
                if not symbol:
                    continue
                
                breakout_date = input("Breakout Date (YYYY-MM-DD): ").strip()
                if not breakout_date:
                    continue
                
                try:
                    datetime.strptime(breakout_date, '%Y-%m-%d')
                except ValueError:
                    print("✗ Invalid date format. Use YYYY-MM-DD")
                    continue
                
                stop_loss_str = input("Stop Loss Price: ").strip()
                try:
                    stop_loss_price = float(stop_loss_str)
                except ValueError:
                    print("✗ Invalid price. Must be a number")
                    continue
                
                entry_price_str = input("Entry Price (optional, press Enter to skip): ").strip()
                entry_price = float(entry_price_str) if entry_price_str else None
                
                notes = input("Notes (optional): ").strip() or None
                
                # Confirm
                print(f"\n  Symbol: {symbol}")
                print(f"  Breakout Date: {breakout_date}")
                print(f"  Stop Loss: ${stop_loss_price}")
                if entry_price:
                    print(f"  Entry Price: ${entry_price}")
                if notes:
                    print(f"  Notes: {notes}")
                
                confirm = input("\nSave this entry? (y/n): ").strip().lower()
                if confirm == 'y':
                    self.add_breakout_metadata(
                        symbol=symbol,
                        breakout_date=breakout_date,
                        stop_loss_price=stop_loss_price,
                        entry_price=entry_price,
                        notes=notes
                    )
                    print(f"✓ Saved!\n")
                else:
                    print("✗ Cancelled\n")
                
                another = input("Add another? (y/n): ").strip().lower()
                if another != 'y':
                    break
                    
        except KeyboardInterrupt:
            print("\n\nExiting...")
        finally:
            self.close()
    
    def display_metadata(self, symbol=None):
        """Display current breakout metadata in formatted table"""
        records = self.get_breakout_metadata(symbol=symbol)
        
        if not records:
            print("\nNo active breakout metadata found.")
            return
        
        print("\n" + "="*100)
        print("Current Breakout Metadata")
        print("="*100)
        print(f"{'Symbol':<8} {'Date':<12} {'Stop Loss':<12} {'Entry':<12} {'Notes':<30} {'Status':<8}")
        print("-"*100)
        
        for record in records:
            status = "ACTIVE" if record['is_active'] else "INACTIVE"
            entry = f"${record['entry_price']:.2f}" if record['entry_price'] else "-"
            stop_loss = f"${record['stop_loss_price']:.2f}"
            notes = (record['notes'] or "")[:27] + "..." if record['notes'] and len(record['notes']) > 30 else (record['notes'] or "-")
            
            print(f"{record['symbol']:<8} {str(record['breakout_date']):<12} {stop_loss:<12} {entry:<12} {notes:<30} {status:<8}")
        
        print("-"*100)
        print(f"Total: {len(records)} records\n")
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions for external use
def add_breakout_metadata(symbol, breakout_date, stop_loss_price, entry_price=None, notes=None):
    """Convenience function to add breakout metadata"""
    with BreakoutInputHandler() as handler:
        return handler.add_breakout_metadata(symbol, breakout_date, stop_loss_price, entry_price, notes)


def get_breakout_metadata(symbol=None, active_only=True):
    """Convenience function to get breakout metadata"""
    with BreakoutInputHandler() as handler:
        return handler.get_breakout_metadata(symbol, active_only)


def get_active_symbols():
    """Convenience function to get active symbols"""
    with BreakoutInputHandler() as handler:
        return handler.get_active_symbols()


if __name__ == "__main__":
    # Interactive mode when run directly
    with BreakoutInputHandler() as handler:
        # First show current metadata
        handler.display_metadata()
        
        # Then start interactive input
        print("\nOptions:")
        print("1. Add new breakout metadata")
        print("2. View current metadata")
        print("3. Deactivate a symbol")
        
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == "1":
            handler.interactive_input()
        elif choice == "2":
            handler.display_metadata()
        elif choice == "3":
            symbol = input("Symbol to deactivate: ").strip().upper()
            handler.deactivate_symbol(symbol)
            print(f"✓ Deactivated {symbol}")
