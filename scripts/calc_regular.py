import sqlite3
import json
from typing import Dict, List, Tuple, Set
import re
import unicodedata
from scipy import stats
import numpy as np

class KanjiReadingAnalyzer:
    """
    Analyzes Japanese name readings by mapping pronunciation to orthographic form.
    Loads kanji reading data from SQLite database and analyzes name regularity.
    """
    def __init__(self, db_path: str = 'namae.db'):
        self.kanji_readings = {}  # kanji -> {'kun': set, 'on': set, 'nanori': set}
        self.db_path = db_path
    
    def load_kanjidic(self, table_name: str = 'kanji'):
        """
        Load kanji dictionary data from SQLite database
        
        >>> # This would work with a real database
        >>> # analyzer = KanjiReadingAnalyzer('test.db')
        >>> # analyzer.load_kanjidic('kanji')
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query to get kanji data
            cursor.execute(f"SELECT kanji, kunyomi, onyomi, nanori FROM {table_name}")
            rows = cursor.fetchall()
            
            for row in rows:
                kanji, kunyomi, onyomi, nanori = row
                
                if not kanji:  # Skip empty kanji
                    continue
                    
                # Parse readings, handling empty fields and multiple readings
                kun_readings = set()
                on_readings = set()
                nanori_readings = set()
                
                if kunyomi:
                    # Split by spaces and clean up
                    kun_readings = set(reading.strip() for reading in kunyomi.split() if reading.strip())
                
                if onyomi:
                    # Split by spaces and clean up
                    on_readings = set(reading.strip() for reading in onyomi.split() if reading.strip())
                
                if nanori:
                    # Split by spaces and clean up
                    nanori_readings = set(reading.strip() for reading in nanori.split() if reading.strip())
                
                self.kanji_readings[kanji] = {
                    'kun': kun_readings,
                    'on': on_readings,
                    'nanori': nanori_readings
                }
            
            conn.close()
            print(f"Loaded {len(self.kanji_readings)} kanji from {self.db_path}")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error loading kanji data: {e}")
    
    def _clean_reading(self, reading: str) -> str:
        """Clean up reading by removing special markers (except for kun readings with dots)"""
        # Remove other common markers but preserve dots for kun readings
        reading = re.sub(r'[()-]', '', reading)
        return reading.strip()
    
    def analyze_name_reading(self, orth: str, pron: str) -> List[Tuple[str, str, str]]:
        """
        Analyze a name's reading regularity using backtracking to find optimal parsing.
        
        Algorithm behavior:
        1. Tries to find a complete parsing where all characters have valid readings
        2. Prioritizes shorter readings to allow more characters to match
        3. If no complete parsing exists, falls back to greedy matching
        4. Handles kun readings with dots (e.g., かけ.る matches かける)
        
        Returns list of (character, reading, type) tuples
        
        >>> analyzer = KanjiReadingAnalyzer()
        >>> analyzer.kanji_readings['翔'] = {'kun': {'かけ.る', 'と.ぶ'}, 'on': {'しょう'}, 'nanori': {'か'}}
        >>> result = analyzer.analyze_name_reading('翔', 'かける')
        >>> result
        [('翔', 'かける', 'kun')]
        
        >>> analyzer.kanji_readings['惺'] = {'kun': {'さと.る'}, 'on': {'せい'}, 'nanori': set()}
        >>> result = analyzer.analyze_name_reading('惺', 'さとる')
        >>> result
        [('惺', 'さとる', 'kun')]
        
        >>> analyzer.kanji_readings['敦'] = {'kun': set(), 'on': set(), 'nanori': {'あつ', 'あつし'}}
        >>> analyzer.kanji_readings['士'] = {'kun': {'さむらい'}, 'on': {'し'}, 'nanori': {'ま', 'お'}}
        >>> result = analyzer.analyze_name_reading('敦士', 'あつし')
        >>> result
        [('敦', 'あつ', 'nanori'), ('士', 'し', 'on')]
        
        >>> analyzer.kanji_readings['寿'] = {'kun': set(), 'on': {'す', 'じゅ'}, 'nanori': {'ことぶき'}}
        >>> result = analyzer.analyze_name_reading('寿々', 'すず')
        >>> result
        [('寿', 'す', 'on'), ('々', 'ず', 'repetition')]
        """
        if not orth or not pron:
            return []
        
        # Try backtracking first for optimal parsing
        result = self._find_best_parsing(orth, pron)
        if result is not None:
            return result
        
        # If backtracking fails, fall back to greedy matching
        return self._greedy_parsing(orth, pron)
    
    def _find_best_parsing(self, orth: str, pron: str) -> List[Tuple[str, str, str]]:
        """
        Find the best parsing using backtracking that minimizes irregular readings
        Returns None if no complete parsing is possible
        """
        def backtrack(char_idx: int, pron_idx: int, current_result: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
            # Base case: processed all characters
            if char_idx >= len(orth):
                # Check that we've consumed exactly the full pronunciation
                if pron_idx == len(pron):
                    # Verify concatenated readings match the target pronunciation
                    concatenated = ''.join(reading for _, reading, _ in current_result if reading)
                    if concatenated == pron:
                        return current_result.copy()
                return None  # Either leftover pronunciation or concatenation mismatch
            
            char = orth[char_idx]
            remaining_pron = pron[pron_idx:]
            
            # Handle hiragana characters
            if self._is_hiragana(char):
                if remaining_pron.startswith(char):
                    new_result = current_result + [(char, char, 'hiragana')]
                    final_result = backtrack(char_idx + 1, pron_idx + 1, new_result)
                    if final_result is not None:
                        return final_result
                return None  # Hiragana must match exactly
            
            # Handle katakana characters
            if self._is_katakana(char):
                hiragana_char = self._katakana_to_hiragana(char)
                if remaining_pron.startswith(hiragana_char):
                    new_result = current_result + [(char, hiragana_char, 'katakana')]
                    final_result = backtrack(char_idx + 1, pron_idx + 1, new_result)
                    if final_result is not None:
                        return final_result
                return None  # Katakana must match exactly
            
            # Handle repetition mark 々
            if char == '々':
                if len(current_result) > 0:
                    # Get the reading of the previous character
                    prev_char, prev_reading, prev_type = current_result[-1]
                    
                    if prev_reading and prev_type not in ['irregular', 'unknown']:
                        # Try exact repetition first
                        if remaining_pron.startswith(prev_reading):
                            new_result = current_result + [(char, prev_reading, 'repetition')]
                            final_result = backtrack(char_idx + 1, pron_idx + len(prev_reading), new_result)
                            if final_result is not None:
                                return final_result
                        
                        # Try with dakuten (voiced version)
                        dakuten_reading = self._add_dakuten(prev_reading)
                        if dakuten_reading != prev_reading and remaining_pron.startswith(dakuten_reading):
                            new_result = current_result + [(char, dakuten_reading, 'repetition')]
                            final_result = backtrack(char_idx + 1, pron_idx + len(dakuten_reading), new_result)
                            if final_result is not None:
                                return final_result
                
                return None  # Failed to match repetition mark
            
            # Handle kanji characters
            if char not in self.kanji_readings:
                return None  # Unknown characters prevent complete parsing
            
            # Try all possible readings for this kanji
            possible_matches = []
            
            for reading_type in ['kun', 'on', 'nanori']:
                for reading in self.kanji_readings[char][reading_type]:
                    clean_reading = self._clean_reading(reading)
                    
                    # For kun readings, try both expanded forms
                    if reading_type == 'kun':
                        expanded_readings = self._expand_kun_reading(clean_reading)
                    else:
                        expanded_readings = [clean_reading.replace('.', '')]
                    
                    for expanded_reading in expanded_readings:
                        if remaining_pron.startswith(expanded_reading):
                            possible_matches.append((expanded_reading, reading_type))
            
            # Sort by length (longer first for single character names, shorter first for multi-character)
            # This handles cases like 翔|かける (should use full かける) vs 敦士|あつし (should use あつ+し)
            if len(orth) == 1:
                # Single character: prefer longer matches (complete pronunciation)
                possible_matches.sort(key=lambda x: len(x[0]), reverse=True)
            else:
                # Multiple characters: prefer shorter matches (allow other chars to match)
                possible_matches.sort(key=lambda x: len(x[0]))
            
            # Try each possible match
            for match_reading, match_type in possible_matches:
                new_result = current_result + [(char, match_reading, match_type)]
                final_result = backtrack(char_idx + 1, pron_idx + len(match_reading), new_result)
                if final_result is not None:
                    return final_result
            
            return None  # No valid reading found
        
        return backtrack(0, 0, [])
    
    def _greedy_parsing(self, orth: str, pron: str) -> List[Tuple[str, str, str]]:
        """
        Fallback greedy parsing when backtracking fails to find complete solution.
        Tries to match as many characters as possible, marking unmatched as irregular.
        """
        result = []
        remaining_pron = pron
        
        for i, char in enumerate(orth):
            # Handle hiragana characters
            if self._is_hiragana(char):
                if remaining_pron.startswith(char):
                    result.append((char, char, 'hiragana'))
                    remaining_pron = remaining_pron[1:]
                else:
                    result.append((char, '', 'irregular'))
                continue
            
            # Handle katakana characters
            if self._is_katakana(char):
                hiragana_char = self._katakana_to_hiragana(char)
                if remaining_pron.startswith(hiragana_char):
                    result.append((char, hiragana_char, 'katakana'))
                    remaining_pron = remaining_pron[1:]
                else:
                    result.append((char, '', 'irregular'))
                continue
            
            # Handle repetition mark 々
            if char == '々':
                if len(result) > 0:
                    # Get the reading of the previous character
                    prev_char, prev_reading, prev_type = result[-1]
                    
                    if prev_reading and prev_type not in ['irregular', 'unknown']:
                        # Try exact repetition first
                        if remaining_pron.startswith(prev_reading):
                            result.append((char, prev_reading, 'repetition'))
                            remaining_pron = remaining_pron[len(prev_reading):]
                            continue
                        
                        # Try with dakuten (voiced version)
                        dakuten_reading = self._add_dakuten(prev_reading)
                        if dakuten_reading != prev_reading and remaining_pron.startswith(dakuten_reading):
                            result.append((char, dakuten_reading, 'repetition'))
                            remaining_pron = remaining_pron[len(dakuten_reading):]
                            continue
                
                # If repetition matching failed
                result.append((char, '', 'irregular'))
                continue
            
            # Handle kanji characters
            if char not in self.kanji_readings:
                result.append((char, '', 'unknown'))
                continue
            
            # Find best match for this character
            possible_matches = []
            
            for reading_type in ['kun', 'on', 'nanori']:
                for reading in self.kanji_readings[char][reading_type]:
                    clean_reading = self._clean_reading(reading)
                    
                    # For kun readings, try both expanded forms
                    if reading_type == 'kun':
                        expanded_readings = self._expand_kun_reading(clean_reading)
                    else:
                        expanded_readings = [clean_reading.replace('.', '')]
                    
                    for expanded_reading in expanded_readings:
                        if remaining_pron.startswith(expanded_reading):
                            possible_matches.append((expanded_reading, reading_type))
            
            # Choose best match based on context
            if possible_matches:
                if len(orth) == 1:
                    # Single character: prefer the match that consumes all remaining pronunciation
                    best_match = None
                    for reading, reading_type in possible_matches:
                        if reading == remaining_pron:  # Exact match for remaining pronunciation
                            best_match = (reading, reading_type)
                            break
                    
                    # If no exact match, prefer longest match
                    if best_match is None:
                        best_match = max(possible_matches, key=lambda x: len(x[0]))
                else:
                    # Multiple characters: prefer shorter matches (greedy but allow others to match)
                    best_match = min(possible_matches, key=lambda x: len(x[0]))
                
                result.append((char, best_match[0], best_match[1]))
                remaining_pron = remaining_pron[len(best_match[0]):]
            else:
                result.append((char, '', 'irregular'))
        
        return result
    
    def _is_hiragana(self, char: str) -> bool:
        """Check if character is hiragana"""
        return 'HIRAGANA' in unicodedata.name(char, '')
    
    def _is_katakana(self, char: str) -> bool:
        """Check if character is katakana"""
        return 'KATAKANA' in unicodedata.name(char, '')
    
    def _katakana_to_hiragana(self, char: str) -> str:
        """Convert katakana character to hiragana"""
        if self._is_katakana(char):
            # Convert katakana to hiragana by shifting Unicode value
            # Katakana starts at U+30A1, hiragana at U+3041
            return chr(ord(char) - 0x60)
        return char
    
    def _add_dakuten(self, reading: str) -> str:
        """
        Add dakuten (voiced marks) to a reading if possible.
        
        >>> analyzer = KanjiReadingAnalyzer()
        >>> analyzer._add_dakuten('す')
        'ず'
        >>> analyzer._add_dakuten('こ')
        'ご'
        >>> analyzer._add_dakuten('か')
        'が'
        >>> analyzer._add_dakuten('み')
        'み'
        """
        # Dakuten conversion table
        dakuten_map = {
            'か': 'が', 'き': 'ぎ', 'く': 'ぐ', 'け': 'げ', 'こ': 'ご',
            'さ': 'ざ', 'し': 'じ', 'す': 'ず', 'せ': 'ぜ', 'そ': 'ぞ',
            'た': 'だ', 'ち': 'ぢ', 'つ': 'づ', 'て': 'で', 'と': 'ど',
            'は': 'ば', 'ひ': 'び', 'ふ': 'ぶ', 'へ': 'べ', 'ほ': 'ぼ',
            'ぱ': 'ば', 'ぴ': 'び', 'ぷ': 'ぶ', 'ぺ': 'べ', 'ぽ': 'ぼ'
        }
        
        return dakuten_map.get(reading, reading)
        """Convert katakana character to hiragana"""
        if self._is_katakana(char):
            # Convert katakana to hiragana by shifting Unicode value
            # Katakana starts at U+30A1, hiragana at U+3041
            return chr(ord(char) - 0x60)
        return char
    
    def _expand_kun_reading(self, reading: str) -> List[str]:
        """
        Expand kun readings with dots to include both forms.
        
        >>> analyzer = KanjiReadingAnalyzer()
        >>> analyzer._expand_kun_reading('くぼ.む')
        ['くぼ', 'くぼむ']
        >>> analyzer._expand_kun_reading('うつく.しい')
        ['うつく', 'うつくしい']
        >>> analyzer._expand_kun_reading('かけ.る')
        ['かけ', 'かける']
        >>> analyzer._expand_kun_reading('あか')
        ['あか']
        """
        if '.' in reading:
            # Split at the dot and return both the stem and full form (with dot removed)
            stem = reading.split('.')[0]
            full_form = reading.replace('.', '')
            return [stem, full_form]
        return [reading]
    
    def analyze_names_from_db(self, table_name: str = 'namae') -> Dict[str, List[Tuple[str, str, str]]]:
        """Analyze all names from SQLite database"""
        results = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query to get names data
            cursor.execute(f"SELECT nid, orth, pron FROM {table_name}")
            rows = cursor.fetchall()
            
            for i, row in enumerate(rows):
                nid, orth, pron = row
                
                if orth and pron:
                    try:
                        analysis = self.analyze_name_reading(orth, pron)
                        results[f"{nid}:{orth}|{pron}"] = analysis
                    except Exception as e:
                        print(f"Error at record {i+1} (nid={nid}): {orth}|{pron}")
                        print(f"Error: {e}")
                        import traceback
                        traceback.print_exc()
                        break
            
            conn.close()
            print(f"Analyzed {len(results)} names from database")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error analyzing names: {e}")
        
        return results
    
    def analyze_names_by_demographics(self, table_name: str = 'namae') -> Dict[str, Dict]:
        """
        Analyze names with demographic information (year, gender)
        Returns detailed results with demographic breakdowns
        """
        results = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query to get names data with demographics
            cursor.execute(f"SELECT nid, year, orth, pron, gender FROM {table_name}")
            rows = cursor.fetchall()
            
            for row in rows:
                nid, year, orth, pron, gender = row
                
                if orth and pron:
                    analysis = self.analyze_name_reading(orth, pron)
                    results[f"{nid}:{orth}|{pron}"] = {
                        'analysis': analysis,
                        'year': year,
                        'gender': gender,
                        'orth': orth,
                        'pron': pron,
                        'nid': nid
                    }
            
            conn.close()
            print(f"Analyzed {len(results)} names with demographics from database")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error analyzing names: {e}")
        
        return results
    
    def calculate_irregularity_by_demographics(self, table_name: str = 'namae') -> Dict[str, Dict]:
        """
        Calculate proportion of names with irregular readings by year and gender
        
        Returns structure like:
        {
            'by_year': {2008: {'total': 100, 'irregular': 25, 'proportion': 0.25}, ...},
            'by_gender': {'M': {'total': 500, 'irregular': 75, 'proportion': 0.15}, ...},
            'by_year_gender': {
                2008: {'M': {'total': 50, 'irregular': 10, 'proportion': 0.2}, ...},
                ...
            },
            'overall': {'total': 1000, 'irregular': 150, 'proportion': 0.15}
        }
        """
        # Get detailed analysis results
        detailed_results = self.analyze_names_by_demographics(table_name)
        
        # Initialize counters
        by_year = {}
        by_gender = {}
        by_year_gender = {}
        overall_total = 0
        overall_irregular = 0
        
        for name_key, data in detailed_results.items():
            analysis = data['analysis']
            year = data['year']
            gender = data['gender']
            
            # Check if name has any irregular readings
            has_irregular = any(reading_type == 'irregular' for _, _, reading_type in analysis)
            
            # Update overall counters
            overall_total += 1
            if has_irregular:
                overall_irregular += 1
            
            # Update by year
            if year not in by_year:
                by_year[year] = {'total': 0, 'irregular': 0}
            by_year[year]['total'] += 1
            if has_irregular:
                by_year[year]['irregular'] += 1
            
            # Update by gender
            if gender not in by_gender:
                by_gender[gender] = {'total': 0, 'irregular': 0}
            by_gender[gender]['total'] += 1
            if has_irregular:
                by_gender[gender]['irregular'] += 1
            
            # Update by year and gender
            if year not in by_year_gender:
                by_year_gender[year] = {}
            if gender not in by_year_gender[year]:
                by_year_gender[year][gender] = {'total': 0, 'irregular': 0}
            by_year_gender[year][gender]['total'] += 1
            if has_irregular:
                by_year_gender[year][gender]['irregular'] += 1
        
        # Calculate proportions
        for year_data in by_year.values():
            year_data['proportion'] = year_data['irregular'] / year_data['total'] if year_data['total'] > 0 else 0
        
        for gender_data in by_gender.values():
            gender_data['proportion'] = gender_data['irregular'] / gender_data['total'] if gender_data['total'] > 0 else 0
        
        for year_dict in by_year_gender.values():
            for gender_data in year_dict.values():
                gender_data['proportion'] = gender_data['irregular'] / gender_data['total'] if gender_data['total'] > 0 else 0
        
        overall_proportion = overall_irregular / overall_total if overall_total > 0 else 0
        
        return {
            'by_year': by_year,
            'by_gender': by_gender,
            'by_year_gender': by_year_gender,
            'overall': {
                'total': overall_total,
                'irregular': overall_irregular,
                'proportion': overall_proportion
            }
        }
    
    def print_irregularity_report(self, table_name: str = 'namae', data: str = None):
        """
        Print a formatted report of irregularity statistics
        
        Args:
            table_name: Name of the database table to analyze
            data: Optional path to save JSON data (e.g., 'path/irregular.json')
        """
        irregularity_stats = self.calculate_irregularity_by_demographics(table_name)
        
        print("=" * 60)
        print("JAPANESE NAME READING IRREGULARITY REPORT")
        print("=" * 60)
        
        # Overall statistics
        overall = irregularity_stats['overall']
        print(f"\nOVERALL STATISTICS:")
        print(f"Total names analyzed: {overall['total']}")
        print(f"Names with irregular readings: {overall['irregular']}")
        print(f"Proportion irregular: {overall['proportion']:.1%}")
        
        # By year
        print(f"\nBY YEAR:")
        print(f"{'Year':<6} {'Total':<8} {'Irregular':<10} {'Proportion':<12}")
        print("-" * 40)
        for year in sorted(irregularity_stats['by_year'].keys()):
            data_row = irregularity_stats['by_year'][year]
            print(f"{year:<6} {data_row['total']:<8} {data_row['irregular']:<10} {data_row['proportion']:<12.1%}")
        
        # By gender
        print(f"\nBY GENDER:")
        print(f"{'Gender':<8} {'Total':<8} {'Irregular':<10} {'Proportion':<12}")
        print("-" * 42)
        for gender in sorted(irregularity_stats['by_gender'].keys()):
            data_row = irregularity_stats['by_gender'][gender]
            print(f"{gender:<8} {data_row['total']:<8} {data_row['irregular']:<10} {data_row['proportion']:<12.1%}")
        
        # By year and gender (condensed view)
        print(f"\nBY YEAR AND GENDER:")
        years = sorted(irregularity_stats['by_year_gender'].keys())
        genders = sorted(set().union(*[year_dict.keys() for year_dict in irregularity_stats['by_year_gender'].values()]))
        
        # Header
        header = f"{'Year':<6}"
        for gender in genders:
            header += f" {gender}(Tot/Irr/%)  "
        print(header)
        print("-" * len(header))
        
        # Data rows
        for year in years:
            row = f"{year:<6}"
            for gender in genders:
                if gender in irregularity_stats['by_year_gender'][year]:
                    data_row = irregularity_stats['by_year_gender'][year][gender]
                    row += f" {data_row['total']:3}/{data_row['irregular']:3}/{data_row['proportion']:4.1%} "
                else:
                    row += " " + " " * 12
            print(row)
        
        print("=" * 60)
        
        # Save JSON data if requested
        if data:
            self._save_irregularity_json(irregularity_stats, data)
        
        # Statistical tests
        self._run_statistical_tests(irregularity_stats)
    
    def _run_statistical_tests(self, irregularity_stats: Dict):
        """
        Run statistical tests on irregularity data
        
        (i) Trend over time: Uses Spearman rank correlation to test if irregularity 
            is significantly increasing/decreasing over time. Spearman is chosen because:
            - It's non-parametric (doesn't assume normal distribution)
            - It detects monotonic relationships (consistent increase/decrease)
            - It's robust to outliers
        
        (ii) Gender differences: Uses Chi-square test of independence to test if 
             gender and irregularity are significantly associated. Chi-square is chosen because:
             - It tests categorical variables (gender vs irregular/regular)
             - It compares observed vs expected frequencies
             - It's appropriate for count data
        """
        print("\n" + "=" * 60)
        print("STATISTICAL TESTS")
        print("=" * 60)
        
        # Test 1: Trend over time (Spearman correlation)
        years = sorted(irregularity_stats['by_year'].keys())
        proportions = [irregularity_stats['by_year'][year]['proportion'] for year in years]
        
        if len(years) > 2:  # Need at least 3 points for meaningful correlation
            spearman_corr, spearman_p = stats.spearmanr(years, proportions)
            
            print(f"\n1. TREND OVER TIME (Spearman Rank Correlation)")
            print(f"   Correlation coefficient: {spearman_corr:.4f}")
            print(f"   P-value: {spearman_p:.4f}")
            
            if spearman_p < 0.05:
                trend_direction = "increasing" if spearman_corr > 0 else "decreasing"
                print(f"   Result: Irregularity is SIGNIFICANTLY {trend_direction} over time")
            else:
                print(f"   Result: NO significant trend over time")
            
            print(f"   Interpretation: Spearman correlation tests for monotonic trends")
            print(f"   without assuming linear relationship or normal distribution.")
        else:
            print(f"\n1. TREND OVER TIME: Insufficient data (need ≥3 years)")
        
        # Test 2: Gender differences (Chi-square test)
        gender_data = irregularity_stats['by_gender']
        if len(gender_data) >= 2:
            # Create contingency table: [irregular_counts, regular_counts] for each gender
            genders = sorted(gender_data.keys())
            contingency_table = []
            
            for gender in genders:
                irregular = gender_data[gender]['irregular']
                regular = gender_data[gender]['total'] - irregular
                contingency_table.append([irregular, regular])
            
            contingency_table = np.array(contingency_table)
            
            # Perform chi-square test
            chi2, chi2_p, dof, expected = stats.chi2_contingency(contingency_table)
            
            print(f"\n2. GENDER DIFFERENCES (Chi-square Test of Independence)")
            print(f"   Chi-square statistic: {chi2:.4f}")
            print(f"   P-value: {chi2_p:.4f}")
            print(f"   Degrees of freedom: {dof}")
            
            if chi2_p < 0.05:
                print(f"   Result: Gender and irregularity are SIGNIFICANTLY associated")
                
                # Show which gender has higher irregularity
                gender_props = {g: gender_data[g]['proportion'] for g in genders}
                highest_gender = max(gender_props.keys(), key=lambda g: gender_props[g])
                print(f"   {highest_gender} names have higher irregularity rate")
            else:
                print(f"   Result: NO significant association between gender and irregularity")
            
            print(f"   Interpretation: Chi-square tests if gender and reading irregularity")
            print(f"   are independent (H0) or associated (H1).")
            
            # Show contingency table
            print(f"\n   Contingency Table:")
            print(f"   {'Gender':<8} {'Irregular':<12} {'Regular':<12} {'Total':<12}")
            print(f"   {'-'*48}")
            for i, gender in enumerate(genders):
                irregular_count = contingency_table[i][0]
                regular_count = contingency_table[i][1]
                total_count = irregular_count + regular_count
                print(f"   {gender:<8} {irregular_count:<12} {regular_count:<12} {total_count:<12}")
        else:
            print(f"\n2. GENDER DIFFERENCES: Insufficient data (need ≥2 genders)")
        
        print("=" * 60)
    
    def _save_irregularity_json(self, stats: Dict, filepath: str):
        """Save irregularity statistics as JSON in table format"""
        try:
            # Prepare data for JSON export in table format
            json_data = {
                "by_year": {
                    "headers": ["Year", "Total", "Irregular", "Proportion"],
                    "rows": [],
                    "caption": "Name Reading Irregularity by Year"
                },
                "by_gender": {
                    "headers": ["Gender", "Total", "Irregular", "Proportion"],
                    "rows": [],
                    "caption": "Name Reading Irregularity by Gender"
                },
                "by_year_gender": {
                    "headers": ["Year", "Gender", "Total", "Irregular", "Proportion"],
                    "rows": [],
                    "caption": "Name Reading Irregularity by Year and Gender"
                }
            }
            
            # Fill by_year data
            for year in sorted(stats['by_year'].keys()):
                data_row = stats['by_year'][year]
                json_data["by_year"]["rows"].append([
                    str(year),
                    str(data_row['total']),
                    str(data_row['irregular']),
                    f"{data_row['proportion']:.3f}"
                ])
            
            # Fill by_gender data
            for gender in sorted(stats['by_gender'].keys()):
                data_row = stats['by_gender'][gender]
                json_data["by_gender"]["rows"].append([
                    gender,
                    str(data_row['total']),
                    str(data_row['irregular']),
                    f"{data_row['proportion']:.3f}"
                ])
            
            # Fill by_year_gender data
            for year in sorted(stats['by_year_gender'].keys()):
                for gender in sorted(stats['by_year_gender'][year].keys()):
                    data_row = stats['by_year_gender'][year][gender]
                    json_data["by_year_gender"]["rows"].append([
                        str(year),
                        gender,
                        str(data_row['total']),
                        str(data_row['irregular']),
                        f"{data_row['proportion']:.3f}"
                    ])
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"\nIrregularity data saved to: {filepath}")
            
        except Exception as e:
            print(f"Error saving JSON data: {e}")
    
    def print_analysis_results(self, results: Dict[str, List[Tuple[str, str, str]]]):
        """Print analysis results in a readable format"""
        for name_key, analysis in results.items():
            print(f"\n{name_key}:")
            for char, reading, reading_type in analysis:
                if reading_type == 'irregular':
                    # Show available readings for irregular characters
                    if char in self.kanji_readings:
                        available_readings = []
                        for read_type in ['kun', 'on', 'nanori']:
                            if self.kanji_readings[char][read_type]:
                                readings_list = list(self.kanji_readings[char][read_type])
                                available_readings.append(f"{read_type}: {', '.join(readings_list)}")
                        available_str = "; ".join(available_readings) if available_readings else "no readings"
                        print(f"  {char}: IRREGULAR (available: {available_str})")
                    else:
                        print(f"  {char}: IRREGULAR (no matching reading found)")
                elif reading_type == 'unknown':
                    print(f"  {char}: UNKNOWN (not in dictionary)")
                else:
                    print(f"  {char}: '{reading}' ({reading_type})")
    
    def get_regularity_stats(self, results: Dict[str, List[Tuple[str, str, str]]]) -> Dict[str, int]:
        """Get statistics about reading regularity"""
        stats = {
            'total_characters': 0,
            'kun_readings': 0,
            'on_readings': 0,
            'nanori_readings': 0,
            'irregular_readings': 0,
            'unknown_characters': 0
        }
        
        for analysis in results.values():
            for char, reading, reading_type in analysis:
                stats['total_characters'] += 1
                if reading_type == 'kun':
                    stats['kun_readings'] += 1
                elif reading_type == 'on':
                    stats['on_readings'] += 1
                elif reading_type == 'nanori':
                    stats['nanori_readings'] += 1
                elif reading_type == 'irregular':
                    stats['irregular_readings'] += 1
                elif reading_type == 'unknown':
                    stats['unknown_characters'] += 1
                elif reading_type == 'hiragana':
                    stats['hiragana_characters'] = stats.get('hiragana_characters', 0) + 1
                elif reading_type == 'katakana':
                    stats['katakana_characters'] = stats.get('katakana_characters', 0) + 1
                elif reading_type == 'repetition':
                    stats['repetition_characters'] = stats.get('repetition_characters', 0) + 1
        
        return stats

# Example usage:
if __name__ == "__main__":
    analyzer = KanjiReadingAnalyzer('../web/db/namae.db')  # Uses 'namae.db' by default
    analyzer.load_kanjidic()
    #result = analyzer.analyze_name_reading('龍汰', 'りゅうた')
    #print(result)
    results = analyzer.analyze_names_from_db('namae')
    analyzer.print_analysis_results(results)
    rstats = analyzer.get_regularity_stats(results) 
    print(rstats)
    analyzer.print_irregularity_report()
    
    print("KanjiReadingAnalyzer class ready!")
    print("Usage:")
    print("1. analyzer = KanjiReadingAnalyzer('namae.db')  # Default database")
    print("2. analyzer.load_kanjidic()  # Load from 'kanji' table")
    print("3. analyzer.analyze_name_reading('龍汰', 'りゅうた')")
    print("4. analyzer.analyze_names_from_db()  # Analyze from 'namae' table")
    print("5. analyzer.print_irregularity_report()  # Demographics report")
    print("\nRun doctests with: python -m doctest filename.py -v")
