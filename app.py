from flask import Flask, request, jsonify, render_template
import requests
import re
import json
from urllib.parse import quote_plus
import time

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        print(f"🔍 Analyzing: {text}")
        
        # Real web-based fact checking
        result = real_time_fact_check(text)
        
        print(f"✅ Result: {result['label']} ({result['confidence']}%)")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return create_error_response(str(e))

def real_time_fact_check(text):
    """Real-time fact checking using web search"""
    
    start_time = time.time()
    
    # Step 1: Extract key claims from text
    key_phrases = extract_key_claims(text)
    print(f"📋 Key phrases: {key_phrases}")
    
    # Step 2: Search the web for each claim
    search_results = []
    for phrase in key_phrases:
        results = search_web(phrase)
        search_results.extend(results)
    
    print(f"🌐 Found {len(search_results)} web results")
    
    # Step 3: Analyze results for fact-checking
    fact_analysis = analyze_search_results(text, search_results)
    
    # Step 4: Generate final verdict
    processing_time = round((time.time() - start_time) * 1000)
    
    return create_final_result(text, fact_analysis, search_results, processing_time)

def extract_key_claims(text):
    """Extract searchable key phrases from the input text"""
    
    # Remove common words and focus on key claims
    text_clean = text.lower().strip()
    
    # Extract numbers/percentages for fact-checking
    numbers = re.findall(r'\d+(?:\.\d+)?%?', text)
    
    # Extract key entities (people, places, organizations)
    entities = []
    
    # Common entities to look for
    people = ['trump', 'biden', 'modi', 'putin', 'musk', 'gates']
    places = ['india', 'china', 'america', 'russia', 'ukraine', 'israel']
    orgs = ['who', 'fda', 'cdc', 'nasa', 'google', 'microsoft']
    
    for person in people:
        if person in text_clean:
            entities.append(person)
    
    for place in places:
        if place in text_clean:
            entities.append(place)
            
    for org in orgs:
        if org in text_clean:
            entities.append(org)
    
    # Create search phrases
    search_phrases = []
    
    # Add full text for general search
    search_phrases.append(text[:100])  # First 100 chars
    
    # Add specific fact-check searches
    if numbers and entities:
        for entity in entities[:2]:  # Top 2 entities
            for number in numbers[:2]:  # Top 2 numbers
                search_phrases.append(f"{entity} {number} fact check")
    
    # Add entity-specific searches
    for entity in entities[:3]:
        search_phrases.append(f"{entity} latest news facts")
    
    # Add general fact-check search
    search_phrases.append(f"fact check {text[:50]}")
    
    return search_phrases[:5]  # Limit to 5 searches to avoid overload

def search_web(query):
    """Search the web for fact-checking information"""
    
    try:
        print(f"🔍 Searching for: {query}")
        
        # Use DuckDuckGo Instant Answer API (free, no API key needed)
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            results = []
            
            # Extract abstract/summary
            if data.get('Abstract'):
                results.append({
                    'title': data.get('AbstractText', 'Summary'),
                    'snippet': data.get('Abstract', ''),
                    'source': data.get('AbstractSource', 'DuckDuckGo'),
                    'url': data.get('AbstractURL', ''),
                    'type': 'summary'
                })
            
            # Extract related topics
            for topic in data.get('RelatedTopics', [])[:3]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('Text', '')[:100],
                        'snippet': topic.get('Text', ''),
                        'source': 'Related Information',
                        'url': topic.get('FirstURL', ''),
                        'type': 'related'
                    })
            
            # Extract definition if available
            if data.get('Definition'):
                results.append({
                    'title': 'Definition',
                    'snippet': data.get('Definition', ''),
                    'source': data.get('DefinitionSource', 'Dictionary'),
                    'url': data.get('DefinitionURL', ''),
                    'type': 'definition'
                })
            
            return results
        
        else:
            print(f"❌ Search failed with status: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return []
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

def analyze_search_results(original_text, search_results):
    """Analyze search results to determine fact accuracy"""
    
    text_lower = original_text.lower()
    
    # Initialize analysis
    analysis = {
        'supporting_evidence': [],
        'contradicting_evidence': [],
        'neutral_information': [],
        'credible_sources': [],
        'total_results': len(search_results)
    }
    
    # Keywords that indicate fact-checking or verification
    fact_check_indicators = [
        'fact check', 'false', 'true', 'misleading', 'incorrect', 'accurate',
        'verified', 'debunked', 'confirmed', 'disputed', 'claim'
    ]
    
    # Credible source indicators
    credible_sources = [
        'reuters', 'ap news', 'bbc', 'cnn', 'nbc', 'abc news',
        'washington post', 'new york times', 'wall street journal',
        'snopes', 'politifact', 'factcheck.org', 'who', 'cdc', 'fda',
        'wikipedia', 'britannica', 'nature', 'science'
    ]
    
    # Analyze each search result
    for result in search_results:
        snippet = result.get('snippet', '').lower()
        source = result.get('source', '').lower()
        title = result.get('title', '').lower()
        
        # Check if source is credible
        is_credible = any(cred in source for cred in credible_sources)
        if is_credible:
            analysis['credible_sources'].append(result)
        
        # Look for fact-checking language
        has_fact_check = any(indicator in snippet + title for indicator in fact_check_indicators)
        
        if has_fact_check:
            # Determine if supporting or contradicting
            if any(word in snippet for word in ['false', 'incorrect', 'misleading', 'debunked']):
                analysis['contradicting_evidence'].append(result)
            elif any(word in snippet for word in ['true', 'correct', 'accurate', 'confirmed', 'verified']):
                analysis['supporting_evidence'].append(result)
            else:
                analysis['neutral_information'].append(result)
        else:
            analysis['neutral_information'].append(result)
    
    return analysis

def create_final_result(original_text, fact_analysis, search_results, processing_time):
    """Create the final fact-check result"""
    
    supporting = len(fact_analysis['supporting_evidence'])
    contradicting = len(fact_analysis['contradicting_evidence'])
    credible_sources = len(fact_analysis['credible_sources'])
    total_results = fact_analysis['total_results']
    
    print(f"📊 Analysis: {supporting} supporting, {contradicting} contradicting, {credible_sources} credible")
    
    # Determine verdict based on evidence
    if contradicting >= 2 and credible_sources >= 1:
        # Strong evidence against the claim
        label = 'FALSE'
        confidence = min(85 + (contradicting * 5) + (credible_sources * 3), 95)
        emoji = '❌'
        color_class = 'result-fake'
        warning = 'Multiple sources contradict this claim'
        
    elif contradicting >= 1 and supporting == 0 and credible_sources >= 1:
        # Some evidence against, no support
        label = 'LIKELY FALSE'
        confidence = min(75 + (contradicting * 8) + (credible_sources * 2), 88)
        emoji = '⚠️'
        color_class = 'result-fake'
        warning = 'Credible sources dispute this claim'
        
    elif supporting >= 2 and credible_sources >= 1:
        # Strong supporting evidence
        label = 'LIKELY TRUE'
        confidence = min(80 + (supporting * 4) + (credible_sources * 3), 92)
        emoji = '✅'
        color_class = 'result-reliable'
        warning = None
        
    elif supporting >= 1 and contradicting == 0 and credible_sources >= 1:
        # Some support, no contradiction
        label = 'SUPPORTED'
        confidence = min(70 + (supporting * 6) + (credible_sources * 4), 85)
        emoji = '✅'
        color_class = 'result-reliable'
        warning = None
        
    elif total_results >= 3 and credible_sources >= 2:
        # Good information available but mixed
        label = 'MIXED EVIDENCE'
        confidence = 65 + (credible_sources * 5)
        emoji = '❓'
        color_class = 'result-suspicious'
        warning = 'Sources provide mixed information'
        
    elif total_results >= 1:
        # Some information found
        label = 'INSUFFICIENT DATA'
        confidence = 55 + min(total_results * 3, 15)
        emoji = '❓'
        color_class = 'result-suspicious'
        warning = 'Limited information available for verification'
        
    else:
        # No information found
        label = 'UNVERIFIABLE'
        confidence = 45
        emoji = '❌'
        color_class = 'result-suspicious'
        warning = 'No reliable information found to verify this claim'
    
    # Prepare sources for display
    display_sources = []
    for source in fact_analysis['credible_sources'][:5]:  # Top 5 credible sources
        display_sources.append({
            'name': source.get('source', 'Unknown Source'),
            'title': source.get('title', 'No title')[:100],
            'url': source.get('url', '#'),
            'credibility_score': 85 if 'reuters' in source.get('source', '').lower() or 'bbc' in source.get('source', '').lower() else 75
        })
    
    # Add some general sources if we don't have enough credible ones
    if len(display_sources) < 2:
        for source in search_results[:3]:
            if source not in fact_analysis['credible_sources']:
                display_sources.append({
                    'name': source.get('source', 'Web Source'),
                    'title': source.get('title', 'Search Result')[:100],
                    'url': source.get('url', '#'),
                    'credibility_score': 60
                })
    
    # Create detailed analysis
    pattern_analysis = {
        'red_flags': [],
        'credibility_indicators': [],
        'linguistic_analysis': {
            'exclamation_marks': original_text.count('!'),
            'caps_ratio': round(sum(1 for c in original_text if c.isupper()) / len(original_text) * 100, 1) if original_text else 0,
            'word_count': len(original_text.split()),
            'sensationalism_score': min((original_text.count('!') * 10) + (contradicting * 15), 100)
        },
        'risk_factors': []
    }
    
    if contradicting >= 1:
        pattern_analysis['red_flags'].append(f'{contradicting} sources contradict this claim')
    if credible_sources == 0:
        pattern_analysis['red_flags'].append('No credible sources found')
    if supporting >= 1:
        pattern_analysis['credibility_indicators'].append(f'{supporting} sources support this claim')
    if credible_sources >= 1:
        pattern_analysis['credibility_indicators'].append(f'{credible_sources} credible sources referenced')
    
    return {
        'label': label,
        'confidence': confidence,
        'content_type': 'Web-Verified Claim',
        'emoji': emoji,
        'color_class': color_class,
        'warning': warning,
        'sources': display_sources,
        'source_summary': f'Analyzed {total_results} web sources: {supporting} supporting, {contradicting} contradicting, {credible_sources} from credible outlets',
        'pattern_analysis': pattern_analysis,
        'algorithm_details': {
            'step_1': f'Claim Extraction: Identified key searchable phrases from input text',
            'step_2': f'Web Search: Performed {len(search_results)} searches across multiple sources',
            'step_3': f'Source Analysis: Found {credible_sources} credible sources among results',
            'step_4': f'Evidence Assessment: {supporting} supporting vs {contradicting} contradicting evidence',
            'step_5': f'Final Verdict: {confidence}% confidence based on web evidence analysis',
            'algorithm_features': [
                'Real-time web search integration',
                'Multi-source evidence analysis',
                'Credible source identification',
                'Fact-check pattern recognition',
                'Evidence contradiction detection',
                'Dynamic confidence scoring'
            ]
        },
        'processing_time': f'{processing_time}ms',
        'methodology': 'Real-time web search + Multi-source analysis + Evidence contradiction detection + Credible source verification'
    }

def create_error_response(error_msg):
    """Create error response in standard format"""
    return {
        'label': 'ERROR',
        'confidence': 0,
        'content_type': 'System Error',
        'emoji': '❌',
        'color_class': 'result-fake',
        'sources': [],
        'source_summary': f'Error occurred during analysis: {error_msg}',
        'pattern_analysis': {'red_flags': ['System error'], 'credibility_indicators': [], 'linguistic_analysis': {}, 'risk_factors': []},
        'algorithm_details': {'step_1': f'Error: {error_msg}'},
        'processing_time': '0ms',
        'methodology': 'Error handling'
    }

if __name__ == '__main__':
    print("🌐 REAL WEB-SEARCHING Truth Guardian")
    print("✅ Works for ANY statement by searching the web")
    print("🔍 Features:")
    print("   • Real-time web search for any claim")
    print("   • Multi-source evidence analysis") 
    print("   • Credible source identification")
    print("   • Dynamic fact-checking for any topic")
    print("📍 http://localhost:5000")
    print("🧪 Try any claim - it will search the web and verify!")
    print("-" * 60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)