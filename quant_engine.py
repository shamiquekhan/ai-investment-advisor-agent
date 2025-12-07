"""
Quantitative Research Engine for Investment Analysis
Implements factor analysis, anomaly detection, forecasting, and causal inference
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


class FactorAnalysisEngine:
    """
    Analyzes which factors actually predict stock performance
    Returns statistically significant factors with p-values and effect sizes
    """
    
    def __init__(self, stock_data: pd.DataFrame):
        self.data = stock_data
        self.significant_threshold = 0.05
        
    def analyze_factors(self) -> List[Dict[str, Any]]:
        """
        Perform factor analysis on stock metrics
        Returns list of factors with statistical significance
        """
        factors = []
        
        # Define factors to analyze
        factor_definitions = {
            'price_change': 'Price momentum',
            'rsi': 'Technical strength',
            'pe': 'Valuation',
            'marketCap': 'Market size',
            'volume': 'Liquidity',
            'dividend': 'Income potential'
        }
        
        if 'score' not in self.data.columns:
            return factors
            
        target = self.data['score']
        
        for factor_col, factor_name in factor_definitions.items():
            if factor_col not in self.data.columns:
                continue
                
            # Calculate correlation and p-value
            factor_data = pd.to_numeric(self.data[factor_col], errors='coerce')
            valid_mask = ~(factor_data.isna() | target.isna())
            
            if valid_mask.sum() < 3:
                continue
                
            correlation, p_value = stats.pearsonr(
                factor_data[valid_mask],
                target[valid_mask]
            )
            
            # Calculate effect size (Cohen's d)
            high_score = target[valid_mask] > target[valid_mask].median()
            low_score = ~high_score
            
            if high_score.sum() > 0 and low_score.sum() > 0:
                mean_diff = factor_data[valid_mask][high_score].mean() - factor_data[valid_mask][low_score].mean()
                pooled_std = np.sqrt((factor_data[valid_mask][high_score].std()**2 + 
                                     factor_data[valid_mask][low_score].std()**2) / 2)
                effect_size = mean_diff / pooled_std if pooled_std > 0 else 0
            else:
                effect_size = 0
            
            factors.append({
                'factor': factor_name,
                'column': factor_col,
                'correlation': correlation,
                'p_value': p_value,
                'effect_size': effect_size,
                'significant': p_value < self.significant_threshold,
                'strength': self._classify_effect_size(abs(effect_size))
            })
        
        # Sort by significance
        factors.sort(key=lambda x: (not x['significant'], x['p_value']))
        return factors
    
    def _classify_effect_size(self, effect_size: float) -> str:
        """Classify effect size magnitude"""
        if effect_size < 0.2:
            return 'NEGLIGIBLE'
        elif effect_size < 0.5:
            return 'SMALL'
        elif effect_size < 0.8:
            return 'MEDIUM'
        else:
            return 'LARGE'
    
    def get_significant_factors(self) -> List[Dict[str, Any]]:
        """Get only statistically significant factors"""
        all_factors = self.analyze_factors()
        return [f for f in all_factors if f['significant']]
    
    def get_red_herrings(self) -> List[Dict[str, Any]]:
        """Get factors that seem important but aren't statistically significant"""
        all_factors = self.analyze_factors()
        return [f for f in all_factors if not f['significant'] and abs(f['correlation']) > 0.1]


class AnomalyDetector:
    """
    Detects hidden gems (undervalued) and red flags (overvalued)
    Uses Isolation Forest for anomaly detection
    """
    
    def __init__(self, stock_data: pd.DataFrame):
        self.data = stock_data
        self.model = IsolationForest(contamination=0.1, random_state=42)
        
    def detect_anomalies(self) -> pd.DataFrame:
        """
        Detect anomalous stocks (both opportunities and risks)
        Returns DataFrame with anomaly scores and types
        """
        # Select numeric features for anomaly detection
        feature_cols = ['score', 'price', 'change', 'rsi', 'marketCap', 'volume']
        available_cols = [col for col in feature_cols if col in self.data.columns]
        
        if len(available_cols) < 2:
            return pd.DataFrame()
        
        # Prepare data
        X = self.data[available_cols].copy()
        for col in available_cols:
            X[col] = pd.to_numeric(X[col], errors='coerce')
        
        # Remove rows with too many NaNs
        X = X.dropna(thresh=len(available_cols) // 2)
        
        if len(X) < 3:
            return pd.DataFrame()
        
        # Fill remaining NaNs with median
        X = X.fillna(X.median())
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Detect anomalies
        anomaly_scores = self.model.fit_predict(X_scaled)
        anomaly_scores_continuous = self.model.score_samples(X_scaled)
        
        # Create results DataFrame
        results = self.data.loc[X.index].copy()
        results['anomaly_score'] = anomaly_scores_continuous
        results['is_anomaly'] = anomaly_scores == -1
        
        # Classify anomalies as hidden gems or red flags
        results['anomaly_type'] = 'NORMAL'
        
        # Hidden gems: Low score but strong fundamentals
        hidden_gem_mask = (
            results['is_anomaly'] & 
            (results['anomaly_score'] < -0.2) &
            (results['change'] > 0) &
            (results['rsi'] > 50)
        )
        results.loc[hidden_gem_mask, 'anomaly_type'] = 'HIDDEN_GEM'
        
        # Red flags: High score but weak fundamentals or high volatility
        red_flag_mask = (
            results['is_anomaly'] & 
            (results['anomaly_score'] < -0.2) &
            ((results['change'] < -5) | (results['rsi'] < 30))
        )
        results.loc[red_flag_mask, 'anomaly_type'] = 'RED_FLAG'
        
        return results[results['is_anomaly']].sort_values('anomaly_score')
    
    def get_hidden_gems(self) -> pd.DataFrame:
        """Get stocks that are undervalued opportunities"""
        anomalies = self.detect_anomalies()
        if anomalies.empty:
            return pd.DataFrame()
        return anomalies[anomalies['anomaly_type'] == 'HIDDEN_GEM']
    
    def get_red_flags(self) -> pd.DataFrame:
        """Get stocks with warning signals"""
        anomalies = self.detect_anomalies()
        if anomalies.empty:
            return pd.DataFrame()
        return anomalies[anomalies['anomaly_type'] == 'RED_FLAG']


class MarketSegmentation:
    """
    Clusters stocks into segments for portfolio allocation
    E.g., Growth, Value, Income, Speculative
    """
    
    def __init__(self, stock_data: pd.DataFrame, n_clusters: int = 4):
        self.data = stock_data
        self.n_clusters = n_clusters
        self.cluster_model = KMeans(n_clusters=n_clusters, random_state=42)
        
    def perform_clustering(self) -> pd.DataFrame:
        """
        Cluster stocks into market segments
        Returns DataFrame with cluster assignments and characteristics
        """
        # Select features for clustering
        feature_cols = ['score', 'change', 'rsi', 'pe', 'dividend', 'marketCap']
        available_cols = [col for col in feature_cols if col in self.data.columns]
        
        if len(available_cols) < 2:
            return pd.DataFrame()
        
        # Prepare data
        X = self.data[available_cols].copy()
        for col in available_cols:
            X[col] = pd.to_numeric(X[col], errors='coerce')
        
        X = X.dropna(thresh=len(available_cols) // 2)
        
        if len(X) < self.n_clusters:
            return pd.DataFrame()
        
        X = X.fillna(X.median())
        
        # Standardize and cluster
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        clusters = self.cluster_model.fit_predict(X_scaled)
        
        # Create results
        results = self.data.loc[X.index].copy()
        results['cluster'] = clusters
        
        # Name clusters based on characteristics
        cluster_names = self._name_clusters(results)
        results['cluster_name'] = results['cluster'].map(cluster_names)
        
        return results
    
    def _name_clusters(self, data: pd.DataFrame) -> Dict[int, str]:
        """Assign meaningful names to clusters based on their characteristics"""
        cluster_stats = data.groupby('cluster').agg({
            'score': 'mean',
            'change': 'mean',
            'marketCap': 'mean'
        })
        
        names = {}
        for cluster_id in cluster_stats.index:
            score_avg = cluster_stats.loc[cluster_id, 'score']
            change_avg = cluster_stats.loc[cluster_id, 'change']
            
            if score_avg > 7 and change_avg > 2:
                names[cluster_id] = "🚀 Rocket Ships"
            elif score_avg > 6 and abs(change_avg) < 2:
                names[cluster_id] = "💰 Stable Growth"
            elif score_avg < 5 and change_avg > 3:
                names[cluster_id] = "📈 Emerging"
            else:
                names[cluster_id] = "🔷 Value Play"
        
        return names
    
    def get_allocation_strategy(self, total_capital: float) -> Dict[str, float]:
        """
        Suggest portfolio allocation across clusters
        Returns dictionary of cluster name to allocation amount
        """
        clusters = self.perform_clustering()
        if clusters.empty:
            return {}
        
        # Allocation strategy based on cluster risk/reward
        allocation_rules = {
            "🚀 Rocket Ships": 0.30,      # High risk/high reward
            "💰 Stable Growth": 0.40,     # Core holdings
            "📈 Emerging": 0.20,          # Speculative
            "🔷 Value Play": 0.10         # Opportunistic
        }
        
        available_clusters = clusters['cluster_name'].unique()
        total_weight = sum(allocation_rules.get(c, 0) for c in available_clusters)
        
        # Normalize allocations
        allocations = {}
        for cluster_name in available_clusters:
            weight = allocation_rules.get(cluster_name, 0)
            allocations[cluster_name] = (weight / total_weight) * total_capital if total_weight > 0 else 0
        
        return allocations


class QuantitativeAdvisor:
    """
    Main class that combines all quant engines
    Generates comprehensive investment recommendations
    """
    
    def __init__(self, stock_data: pd.DataFrame):
        self.data = stock_data
        self.factor_engine = FactorAnalysisEngine(stock_data)
        self.anomaly_detector = AnomalyDetector(stock_data)
        self.segmentation = MarketSegmentation(stock_data)
    
    def generate_investment_thesis(self, ticker: str) -> Dict[str, Any]:
        """
        Generate comprehensive investment thesis for a stock
        Combines factor analysis, anomaly detection, and clustering
        """
        stock = self.data[self.data['ticker'] == ticker]
        
        if stock.empty:
            return {'error': 'Stock not found'}
        
        stock = stock.iloc[0]
        
        # Get factor analysis
        significant_factors = self.factor_engine.get_significant_factors()
        red_herrings = self.factor_engine.get_red_herrings()
        
        # Check for anomalies
        anomalies = self.anomaly_detector.detect_anomalies()
        is_anomaly = ticker in anomalies['ticker'].values if not anomalies.empty else False
        anomaly_type = anomalies[anomalies['ticker'] == ticker]['anomaly_type'].values[0] if is_anomaly else 'NORMAL'
        
        # Get cluster
        clusters = self.segmentation.perform_clustering()
        cluster_name = clusters[clusters['ticker'] == ticker]['cluster_name'].values[0] if not clusters.empty else 'Unknown'
        
        # Calculate confidence score
        confidence = self._calculate_confidence(significant_factors, anomaly_type, stock)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            stock, significant_factors, anomaly_type, cluster_name, confidence
        )
        
        return {
            'ticker': ticker,
            'name': stock.get('name', ticker),
            'score': stock.get('score', 0),
            'significant_factors': significant_factors[:3],
            'red_herrings': red_herrings,
            'anomaly_type': anomaly_type,
            'cluster': cluster_name,
            'confidence': confidence,
            'recommendation': recommendation['action'],
            'reasoning': recommendation['reasoning'],
            'risk_level': recommendation['risk_level'],
            'position_size': recommendation['position_size']
        }
    
    def _calculate_confidence(self, factors: List[Dict], anomaly_type: str, stock: pd.Series) -> float:
        """Calculate confidence score based on multiple signals"""
        base_confidence = 0.5
        
        # Add confidence for each significant factor
        base_confidence += len(factors) * 0.1
        
        # Boost for hidden gems
        if anomaly_type == 'HIDDEN_GEM':
            base_confidence += 0.15
        
        # Reduce for red flags
        if anomaly_type == 'RED_FLAG':
            base_confidence -= 0.25
        
        # Boost for high score
        score = float(stock.get('score', 0))
        if score > 7:
            base_confidence += 0.1
        
        return min(max(base_confidence, 0.1), 0.95)
    
    def _generate_recommendation(
        self, stock: pd.Series, factors: List[Dict], 
        anomaly_type: str, cluster: str, confidence: float
    ) -> Dict[str, Any]:
        """Generate actionable recommendation"""
        score = float(stock.get('score', 0))
        
        # Determine action
        if confidence > 0.75 and score > 6.5:
            action = "STRONG BUY"
            risk_level = "MEDIUM"
            position_size = "20-30%"
        elif confidence > 0.60 and score > 5.5:
            action = "BUY"
            risk_level = "MEDIUM"
            position_size = "15-20%"
        elif anomaly_type == 'RED_FLAG':
            action = "AVOID/SELL"
            risk_level = "HIGH"
            position_size = "0-5%"
        elif score < 5:
            action = "HOLD"
            risk_level = "HIGH"
            position_size = "5-10%"
        else:
            action = "HOLD"
            risk_level = "MEDIUM"
            position_size = "10-15%"
        
        # Generate reasoning
        reasoning_parts = []
        
        if factors:
            top_factor = factors[0]
            reasoning_parts.append(
                f"{top_factor['factor']} is {top_factor['strength'].lower()} "
                f"predictor (p={top_factor['p_value']:.3f})"
            )
        
        if anomaly_type == 'HIDDEN_GEM':
            reasoning_parts.append("Detected as undervalued opportunity")
        elif anomaly_type == 'RED_FLAG':
            reasoning_parts.append("⚠️ Warning signals detected")
        
        reasoning_parts.append(f"Classified as {cluster}")
        
        reasoning = ". ".join(reasoning_parts)
        
        return {
            'action': action,
            'risk_level': risk_level,
            'position_size': position_size,
            'reasoning': reasoning
        }
    
    def get_portfolio_recommendations(self, total_capital: float = 50000) -> Dict[str, Any]:
        """
        Generate complete portfolio recommendations
        """
        # Get allocation strategy
        allocations = self.segmentation.get_allocation_strategy(total_capital)
        
        # Get hidden gems
        gems = self.anomaly_detector.get_hidden_gems()
        
        # Get red flags
        flags = self.anomaly_detector.get_red_flags()
        
        # Get significant factors across all stocks
        significant_factors = self.factor_engine.get_significant_factors()
        
        return {
            'total_capital': total_capital,
            'cluster_allocations': allocations,
            'hidden_gems': gems[['ticker', 'name', 'score', 'anomaly_score']].to_dict('records') if not gems.empty else [],
            'red_flags': flags[['ticker', 'name', 'score', 'anomaly_score']].to_dict('records') if not flags.empty else [],
            'key_factors': significant_factors[:3],
            'market_insights': self._generate_market_insights(significant_factors)
        }
    
    def _generate_market_insights(self, factors: List[Dict]) -> str:
        """Generate human-readable market insights"""
        if not factors:
            return "Insufficient data for market insights"
        
        insights = ["KEY MARKET INSIGHTS:\n"]
        
        for i, factor in enumerate(factors[:3], 1):
            insights.append(
                f"{i}. {factor['factor']}: {factor['strength']} effect "
                f"(correlation: {factor['correlation']:.2f}, p={factor['p_value']:.3f})"
            )
        
        red_herrings = [f for f in factors if not f['significant']]
        if red_herrings:
            insights.append(f"\n⚠️ Don't rely on: {red_herrings[0]['factor']} (p={red_herrings[0]['p_value']:.2f}, not significant)")
        
        return "\n".join(insights)
