"""
Analyze scraped Trustpilot data to extract real-world dispute patterns.

This script processes the scraped reviews and generates insights
to improve the dispute detection engine.
"""

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List
import statistics

sys.path.insert(0, 'src')
from scrapers.utils.text_processor import DisputePatternExtractor


class TrustpilotDataAnalyzer:
    """Analyze Trustpilot reviews to extract dispute patterns."""
    
    def __init__(self, data_file: str = 'data/scraped/trustpilot_comprehensive.json'):
        """
        Initialize analyzer.
        
        Args:
            data_file: Path to scraped Trustpilot data
        """
        self.data_file = Path(data_file)
        self.reviews = []
        self.processor = DisputePatternExtractor()
        
        self._load_data()
    
    def _load_data(self):
        """Load scraped data from JSON file."""
        if not self.data_file.exists():
            print(f"❌ Data file not found: {self.data_file}")
            return
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
            self.reviews = content.get('data', [])
        
        print(f"✅ Loaded {len(self.reviews)} reviews")
    
    def analyze_all(self) -> Dict:
        """
        Run complete analysis on all reviews.
        
        Returns:
            Dictionary with analysis results
        """
        if not self.reviews:
            print("⚠️ No reviews to analyze")
            return {}
        
        print("\n" + "="*60)
        print("📊 TRUSTPILOT DATA ANALYSIS")
        print("="*60)
        
        results = {
            'total_reviews': len(self.reviews),
            'carrier_distribution': self._analyze_carriers(),
            'rating_distribution': self._analyze_ratings(),
            'pattern_statistics': self._analyze_patterns(),
            'delay_statistics': self._analyze_delays(),
            'severity_analysis': self._analyze_severity(),
            'top_keywords': self._analyze_keywords()
        }
        
        self._print_report(results)
        self._save_insights(results)
        
        return results
    
    def _analyze_carriers(self) -> Dict:
        """Analyze distribution of carriers."""
        carriers = [r['carrier'] for r in self.reviews]
        return dict(Counter(carriers))
    
    def _analyze_ratings(self) -> Dict:
        """Analyze distribution of ratings."""
        ratings = [r.get('rating', 0) for r in self.reviews]
        return {
            'distribution': dict(Counter(ratings)),
            'average': statistics.mean(ratings) if ratings else 0,
            'median': statistics.median(ratings) if ratings else 0
        }
    
    def _analyze_patterns(self) -> Dict:
        """Analyze dispute patterns across all reviews."""
        patterns_summary = {
            'delays': 0,
            'losses': 0,
            'damages': 0,
            'proof_issues': 0
        }
        
        for review in self.reviews:
            patterns = review.get('patterns', {})
            if patterns.get('has_delay'):
                patterns_summary['delays'] += 1
            if patterns.get('has_loss'):
                patterns_summary['losses'] += 1
            if patterns.get('has_damage'):
                patterns_summary['damages'] += 1
            if patterns.get('has_proof_issue'):
                patterns_summary['proof_issues'] += 1
        
        # Calculate percentages
        total = len(self.reviews)
        patterns_summary['percentages'] = {
            k: (v / total * 100) if total > 0 else 0 
            for k, v in patterns_summary.items() if k != 'percentages'
        }
        
        return patterns_summary
    
    def _analyze_delays(self) -> Dict:
        """Analyze delay patterns."""
        all_delays = []
        
        for review in self.reviews:
            patterns = review.get('patterns', {})
            for delay in patterns.get('delay_mentions', []):
                value = delay['value']
                unit = delay['unit']
                
                # Convert to days
                if 'heure' in unit:
                    days = value / 24
                elif 'semaine' in unit:
                    days = value * 7
                elif 'mois' in unit:
                    days = value * 30
                else:
                    days = value
                
                all_delays.append(days)
        
        if not all_delays:
            return {'count': 0}
        
        return {
            'count': len(all_delays),
            'average_days': statistics.mean(all_delays),
            'median_days': statistics.median(all_delays),
            'min_days': min(all_delays),
            'max_days': max(all_delays)
        }
    
    def _analyze_severity(self) -> Dict:
        """Analyze severity scores."""
        scores = [
            r.get('patterns', {}).get('severity_score', 0) 
            for r in self.reviews
        ]
        
        if not scores:
            return {}
        
        return {
            'average': statistics.mean(scores),
            'median': statistics.median(scores),
            'min': min(scores),
            'max': max(scores),
            'distribution': dict(Counter([round(s) for s in scores]))
        }
    
    def _analyze_keywords(self) -> Dict:
        """Extract most common keywords from reviews."""
        all_words = []
        
        # Common French stopwords to exclude
        stopwords = {
            'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une',
            'et', 'ou', 'mais', 'donc', 'car', 'que', 'qui',
            'cette', 'ce', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta',
            'son', 'sa', 'ses', 'je', 'tu', 'il', 'elle', 'nous',
            'vous', 'ils', 'elles', 'dans', 'sur', 'pour', 'par',
            'avec', 'sans', 'est', 'sont', 'été', 'avoir', 'être'
        }
        
        for review in self.reviews:
            text = review.get('text', '').lower()
            words = text.split()
            
            # Filter and clean
            words = [
                w.strip('.,!?;:()[]{}\"\'') 
                for w in words 
                if len(w) > 3 and w.strip('.,!?;:()[]{}\"\'') not in stopwords
            ]
            
            all_words.extend(words)
        
        top_30 = Counter(all_words).most_common(30)
        
        return {word: count for word, count in top_30}
    
    def _print_report(self, results: Dict):
        """Print analysis report to console."""
        print("\n📦 CARRIER DISTRIBUTION")
        print("-" * 40)
        for carrier, count in results['carrier_distribution'].items():
            percentage = (count / results['total_reviews']) * 100
            print(f"  {carrier.capitalize()}: {count} ({percentage:.1f}%)")
        
        print("\n⭐ RATING DISTRIBUTION")
        print("-" * 40)
        rating_dist = results['rating_distribution']['distribution']
        for rating in sorted(rating_dist.keys()):
            count = rating_dist[rating]
            percentage = (count / results['total_reviews']) * 100
            stars = "⭐" * rating
            print(f"  {rating} {stars}: {count} ({percentage:.1f}%)")
        
        print(f"\n  Average Rating: {results['rating_distribution']['average']:.2f}/5")
        
        print("\n🔍 DISPUTE PATTERNS")
        print("-" * 40)
        patterns = results['pattern_statistics']
        print(f"  Delays: {patterns['delays']} ({patterns['percentages']['delays']:.1f}%)")
        print(f"  Losses: {patterns['losses']} ({patterns['percentages']['losses']:.1f}%)")
        print(f"  Damages: {patterns['damages']} ({patterns['percentages']['damages']:.1f}%)")
        print(f"  Proof Issues: {patterns['proof_issues']} ({patterns['percentages']['proof_issues']:.1f}%)")
        
        if results['delay_statistics'].get('count', 0) > 0:
            print("\n⏰ DELAY ANALYSIS")
            print("-" * 40)
            delays = results['delay_statistics']
            print(f"  Total Delay Mentions: {delays['count']}")
            print(f"  Average Delay: {delays['average_days']:.1f} days")
            print(f"  Median Delay: {delays['median_days']:.1f} days")
            print(f"  Range: {delays['min_days']:.1f} - {delays['max_days']:.1f} days")
        
        print("\n📊 SEVERITY SCORES")
        print("-" * 40)
        severity = results['severity_analysis']
        if severity:
            print(f"  Average Severity: {severity['average']:.2f}/5")
            print(f"  Median: {severity['median']:.2f}/5")
            print(f"  Range: {severity['min']:.2f} - {severity['max']:.2f}/5")
        
        print("\n🔤 TOP KEYWORDS")
        print("-" * 40)
        top_keywords = results['top_keywords']
        for i, (word, count) in enumerate(list(top_keywords.items())[:15], 1):
            print(f"  {i:2}. {word:20} ({count} mentions)")
        
        print("\n" + "="*60)
    
    def _save_insights(self, results: Dict):
        """Save analysis insights to file."""
        output_file = Path('data/processed/trustpilot_insights.json')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Insights saved to {output_file}")
    
    def generate_detection_rules(self) -> List[str]:
        """
        Generate recommended detection rules based on analysis.
        
        Returns:
            List of suggested rules as strings
        """
        if not self.reviews:
            return []
        
        patterns = self._analyze_patterns()
        delays = self._analyze_delays()
        
        rules = []
        
        # Rule based on delay frequency
        if patterns['percentages']['delays'] > 30:
            if delays.get('average_days', 0) > 0:
                rules.append(
                    f"# Règle 6 : Retards fréquents (basé sur {patterns['delays']} avis)\n"
                    f"# {patterns['percentages']['delays']:.1f}% des avis mentionnent des retards\n"
                    f"# Délai moyen constaté : {delays['average_days']:.1f} jours\n"
                    f"if delay_days > {max(2, delays['median_days'] - 1)}:\n"
                    f"    dispute_score += 1.5\n"
                    f"    recovery_amount = shipping_cost * 1.5"
                )
        
        # Rule based on loss frequency
        if patterns['percentages']['losses'] > 15:
            rules.append(
                f"# Règle 7 : Colis perdus (basé sur {patterns['losses']} avis)\n"
                f"# {patterns['percentages']['losses']:.1f}% des avis mentionnent des pertes\n"
                f"if status == 'lost' or 'perdu' in description.lower():\n"
                f"    dispute_score += 3.0\n"
                f"    recovery_amount = order_total + shipping_cost"
            )
        
        # Rule based on proof issues
        if patterns['percentages']['proof_issues'] > 10:
            rules.append(
                f"# Règle 8 : Problèmes de preuve (basé sur {patterns['proof_issues']} avis)\n"
                f"# {patterns['percentages']['proof_issues']:.1f}% mentionnent des problèmes de POD\n"
                f"if pod_invalid or signature_missing:\n"
                f"    dispute_score += 2.0\n"
                f"    recovery_amount = shipping_cost + 20  # Frais administratifs"
            )
        
        return rules


def main():
    """Run analysis."""
    analyzer = TrustpilotDataAnalyzer()
    
    # Run full analysis
    results = analyzer.analyze_all()
    
    # Generate recommended rules
    print("\n💡 RECOMMENDED DETECTION RULES")
    print("="*60)
    rules = analyzer.generate_detection_rules()
    
    if rules:
        print("\nSuggested additions to dispute_detector.py:\n")
        for rule in rules:
            print(rule)
            print()
    else:
        print("⚠️ Not enough data to generate rules yet")
    
    print("="*60)


if __name__ == "__main__":
    main()
