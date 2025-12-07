"""
Backtesting Engine for AI Investment Advisor
Validates strategy performance with historical data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import yfinance as yf


class BacktestEngine:
    """
    Backtests investment strategies against historical data
    Provides Sharpe ratio, max drawdown, win rate, and benchmark comparisons
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.daily_values = []
        
    def run_backtest(
        self, 
        tickers: List[str], 
        start_date: str, 
        end_date: str,
        strategy_func=None
    ) -> Dict[str, Any]:
        """
        Run backtest over historical period
        
        Args:
            tickers: List of stock symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            strategy_func: Optional custom strategy function
            
        Returns:
            Dictionary with performance metrics
        """
        # Download historical data
        try:
            data = self._fetch_historical_data(tickers, start_date, end_date)
        except Exception as e:
            return {'error': f'Failed to fetch data: {e}'}
        
        if data.empty:
            return {'error': 'No historical data available'}
        
        # Run simulation
        dates = data.index.unique()
        
        for date in dates:
            day_data = data.loc[date]
            
            # Generate signals (simple momentum strategy if no custom strategy)
            if strategy_func:
                signals = strategy_func(day_data, self.positions)
            else:
                signals = self._simple_momentum_strategy(day_data)
            
            # Execute trades
            self._execute_trades(signals, day_data, date)
            
            # Update portfolio value
            portfolio_value = self._calculate_portfolio_value(day_data)
            self.daily_values.append({
                'date': date,
                'value': portfolio_value
            })
        
        # Calculate metrics
        metrics = self._calculate_metrics(start_date, end_date)
        
        return metrics
    
    def _fetch_historical_data(
        self, 
        tickers: List[str], 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """Fetch historical price data from yfinance"""
        data_frames = []
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    hist['ticker'] = ticker
                    hist['returns'] = hist['Close'].pct_change()
                    hist['sma_20'] = hist['Close'].rolling(20).mean()
                    hist['sma_50'] = hist['Close'].rolling(50).mean()
                    data_frames.append(hist)
            except Exception as e:
                print(f"⚠️ Failed to fetch {ticker}: {e}")
        
        if data_frames:
            return pd.concat(data_frames)
        return pd.DataFrame()
    
    def _simple_momentum_strategy(self, day_data: pd.DataFrame) -> Dict[str, str]:
        """
        Simple momentum strategy:
        - BUY if SMA20 > SMA50 (golden cross)
        - SELL if SMA20 < SMA50 (death cross)
        """
        signals = {}
        
        for ticker in day_data['ticker'].unique():
            ticker_data = day_data[day_data['ticker'] == ticker].iloc[0]
            
            sma_20 = ticker_data.get('sma_20', 0)
            sma_50 = ticker_data.get('sma_50', 0)
            
            if pd.notna(sma_20) and pd.notna(sma_50):
                if sma_20 > sma_50 and ticker not in self.positions:
                    signals[ticker] = 'BUY'
                elif sma_20 < sma_50 and ticker in self.positions:
                    signals[ticker] = 'SELL'
        
        return signals
    
    def _execute_trades(
        self, 
        signals: Dict[str, str], 
        day_data: pd.DataFrame, 
        date
    ):
        """Execute buy/sell orders"""
        for ticker, action in signals.items():
            ticker_data = day_data[day_data['ticker'] == ticker]
            if ticker_data.empty:
                continue
                
            price = ticker_data['Close'].iloc[0]
            
            if action == 'BUY' and ticker not in self.positions:
                # Buy with 20% of available capital
                allocation = self.capital * 0.2
                shares = allocation / price
                
                self.positions[ticker] = {
                    'shares': shares,
                    'buy_price': price,
                    'buy_date': date
                }
                self.capital -= allocation
                
                self.trades.append({
                    'date': date,
                    'ticker': ticker,
                    'action': 'BUY',
                    'price': price,
                    'shares': shares,
                    'amount': allocation
                })
            
            elif action == 'SELL' and ticker in self.positions:
                position = self.positions[ticker]
                shares = position['shares']
                sell_value = shares * price
                pnl = sell_value - (shares * position['buy_price'])
                pnl_pct = (price / position['buy_price'] - 1) * 100
                
                self.capital += sell_value
                del self.positions[ticker]
                
                self.trades.append({
                    'date': date,
                    'ticker': ticker,
                    'action': 'SELL',
                    'price': price,
                    'shares': shares,
                    'amount': sell_value,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
    
    def _calculate_portfolio_value(self, day_data: pd.DataFrame) -> float:
        """Calculate current portfolio value"""
        value = self.capital
        
        for ticker, position in self.positions.items():
            ticker_data = day_data[day_data['ticker'] == ticker]
            if not ticker_data.empty:
                current_price = ticker_data['Close'].iloc[0]
                value += position['shares'] * current_price
        
        return value
    
    def _calculate_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not self.daily_values:
            return {'error': 'No data to calculate metrics'}
        
        df = pd.DataFrame(self.daily_values)
        df.set_index('date', inplace=True)
        
        # Total return
        final_value = df['value'].iloc[-1]
        total_return = (final_value / self.initial_capital - 1) * 100
        
        # Calculate returns
        df['returns'] = df['value'].pct_change()
        
        # Sharpe ratio (assuming 252 trading days, 2% risk-free rate)
        excess_returns = df['returns'] - (0.02 / 252)
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / df['returns'].std() if df['returns'].std() > 0 else 0
        
        # Max drawdown
        df['cummax'] = df['value'].cummax()
        df['drawdown'] = (df['value'] / df['cummax'] - 1) * 100
        max_drawdown = df['drawdown'].min()
        
        # Win rate
        winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        total_trades = len([t for t in self.trades if 'pnl' in t])
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in self.trades if t.get('pnl', 0) < 0]
        avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Volatility
        annual_volatility = df['returns'].std() * np.sqrt(252) * 100
        
        # Get benchmark (S&P 500) performance
        benchmark_metrics = self._calculate_benchmark(start_date, end_date)
        
        return {
            'total_return': total_return,
            'final_value': final_value,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'annual_volatility': annual_volatility,
            'benchmark': benchmark_metrics,
            'daily_values': df['value'].tolist(),
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'trades': self.trades
        }
    
    def _calculate_benchmark(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Calculate S&P 500 benchmark performance"""
        try:
            spy = yf.Ticker('SPY')
            hist = spy.history(start=start_date, end=end_date)
            
            if hist.empty:
                return {'return': 0, 'sharpe': 0, 'max_drawdown': 0}
            
            initial_price = hist['Close'].iloc[0]
            final_price = hist['Close'].iloc[-1]
            benchmark_return = (final_price / initial_price - 1) * 100
            
            hist['returns'] = hist['Close'].pct_change()
            excess_returns = hist['returns'] - (0.02 / 252)
            benchmark_sharpe = np.sqrt(252) * excess_returns.mean() / hist['returns'].std() if hist['returns'].std() > 0 else 0
            
            hist['cummax'] = hist['Close'].cummax()
            hist['drawdown'] = (hist['Close'] / hist['cummax'] - 1) * 100
            benchmark_drawdown = hist['drawdown'].min()
            
            return {
                'return': benchmark_return,
                'sharpe': benchmark_sharpe,
                'max_drawdown': benchmark_drawdown
            }
        except Exception as e:
            print(f"⚠️ Benchmark calculation failed: {e}")
            return {'return': 0, 'sharpe': 0, 'max_drawdown': 0}


class ConfidenceInterval:
    """
    Calculate confidence intervals for predictions
    Using bootstrap resampling
    """
    
    @staticmethod
    def calculate_prediction_ci(
        predictions: List[float],
        confidence_level: float = 0.90
    ) -> Dict[str, float]:
        """
        Calculate confidence interval for predictions
        
        Args:
            predictions: List of predicted values
            confidence_level: Confidence level (0.90 = 90%)
            
        Returns:
            Dictionary with lower, upper bounds and confidence
        """
        if not predictions or len(predictions) < 2:
            return {'lower': 0, 'upper': 0, 'confidence': 0}
        
        predictions = np.array(predictions)
        mean_pred = np.mean(predictions)
        
        # Calculate percentiles for confidence interval
        alpha = 1 - confidence_level
        lower_percentile = alpha / 2 * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        lower_bound = np.percentile(predictions, lower_percentile)
        upper_bound = np.percentile(predictions, upper_percentile)
        
        # Confidence score (narrower interval = higher confidence)
        ci_width = upper_bound - lower_bound
        confidence = max(0, min(1, 1 - (ci_width / abs(mean_pred)))) if mean_pred != 0 else 0
        
        return {
            'mean': mean_pred,
            'lower': lower_bound,
            'upper': upper_bound,
            'confidence': confidence * 100,
            'ci_width': ci_width
        }
    
    @staticmethod
    def bootstrap_confidence_interval(
        data: pd.DataFrame,
        metric_func,
        n_iterations: int = 1000,
        confidence_level: float = 0.90
    ) -> Dict[str, float]:
        """
        Bootstrap confidence intervals for any metric
        
        Args:
            data: Input data
            metric_func: Function to calculate metric
            n_iterations: Number of bootstrap iterations
            confidence_level: Confidence level
            
        Returns:
            Confidence interval dictionary
        """
        bootstrap_metrics = []
        
        for _ in range(n_iterations):
            # Resample with replacement
            sample = data.sample(frac=1.0, replace=True)
            metric = metric_func(sample)
            bootstrap_metrics.append(metric)
        
        return ConfidenceInterval.calculate_prediction_ci(
            bootstrap_metrics, 
            confidence_level
        )


def generate_performance_report(backtest_results: Dict[str, Any]) -> str:
    """
    Generate human-readable performance report
    """
    if 'error' in backtest_results:
        return f"❌ Error: {backtest_results['error']}"
    
    report = f"""
📊 BACKTEST PERFORMANCE REPORT
{'='*50}

💰 RETURNS:
   Total Return:     {backtest_results['total_return']:+.2f}%
   Final Value:      ${backtest_results['final_value']:,.2f}
   Initial Capital:  ${backtest_results.get('initial_capital', 100000):,.2f}

📈 RISK METRICS:
   Sharpe Ratio:     {backtest_results['sharpe_ratio']:.2f}
   Max Drawdown:     {backtest_results['max_drawdown']:.2f}%
   Annual Volatility: {backtest_results['annual_volatility']:.2f}%

🎯 TRADING STATS:
   Total Trades:     {backtest_results['total_trades']}
   Win Rate:         {backtest_results['win_rate']:.1f}%
   Avg Win:          +{backtest_results['avg_win']:.2f}%
   Avg Loss:         {backtest_results['avg_loss']:.2f}%

🏆 VS BENCHMARK (S&P 500):
   Strategy Return:  {backtest_results['total_return']:+.2f}%
   Benchmark Return: {backtest_results['benchmark']['return']:+.2f}%
   Alpha:            {backtest_results['total_return'] - backtest_results['benchmark']['return']:+.2f}%
   
   Strategy Sharpe:  {backtest_results['sharpe_ratio']:.2f}
   Benchmark Sharpe: {backtest_results['benchmark']['sharpe']:.2f}
"""
    
    # Performance verdict
    if backtest_results['total_return'] > backtest_results['benchmark']['return']:
        report += "\n✅ Strategy OUTPERFORMED the market!"
    else:
        report += "\n⚠️ Strategy UNDERPERFORMED the market"
    
    return report
