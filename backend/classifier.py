import re
import os
import yaml
from typing import Dict, Tuple, Optional

class TaxonomyClassifier:
    """Classifier that uses KB.* taxonomy to classify and organize files."""
    
    def __init__(self, taxonomy_path: str):
        """Initialize the classifier with a taxonomy file."""
        self.taxonomy_path = taxonomy_path
        self.taxonomy = self._load_taxonomy()
        self.workspaces = {w['id']: w for w in self.taxonomy['workspaces']}
        self.defaults = self.taxonomy.get('defaults', {})
        
    def _load_taxonomy(self) -> Dict:
        """Load taxonomy from YAML file."""
        with open(self.taxonomy_path, 'r') as f:
            return yaml.safe_load(f)
    
    def classify(self, extracted_text: str, original_filename: str, 
                 text_inference, original_path: str = "") -> Dict:
        """
        Classify a file and generate workspace, subpath, and filename.
        
        Args:
            extracted_text: Text content extracted from the file
            original_filename: Original filename
            text_inference: The NexaTextInference model for LLM classification
            original_path: Full path to original file (optional)
            
        Returns:
            Dict with keys: workspace, subpath, filename, confidence, description
        """
        # Step 1: Extract path hints from original file location
        path_hints = self._extract_path_hints(original_path, original_filename)
        
        # Step 2: Try heuristic rules (now includes path hints)
        heuristic_result = self._apply_heuristics(extracted_text, original_filename, path_hints)
        
        # Step 3: Extract metadata hints from content
        metadata = self._extract_metadata(extracted_text, original_filename)
        
        # Merge path years with content years
        if path_hints and path_hints.get('path_years'):
            metadata['years'] = list(set(metadata['years'] + path_hints['path_years']))
        
        # Step 4: Use LLM for classification
        llm_result = self._classify_with_llm(
            extracted_text, 
            original_filename, 
            metadata,
            text_inference,
            heuristic_hint=heuristic_result,
            path_hints=path_hints
        )
        
        # Step 4: Generate filename with proper prefix
        workspace_id = llm_result['workspace']
        workspace_config = self.workspaces.get(workspace_id, {})
        
        filename = self._generate_filename(
            workspace_config,
            metadata,
            original_filename,
            llm_result.get('suggested_name', '')
        )
        
        return {
            'workspace': workspace_id,
            'subpath': llm_result.get('subpath', ''),
            'filename': filename,
            'confidence': llm_result['confidence'],
            'description': llm_result.get('description', '')
        }
    
    def _extract_path_hints(self, original_path: str, original_filename: str) -> Dict:
        """
        Extract classification hints from the original file path and filename.
        
        Returns dict with:
            - path_keywords: list of keywords from directory names
            - path_years: list of years found in path
            - path_context: combined string of path components
        """
        if not original_path:
            return {'path_keywords': [], 'path_years': [], 'path_context': ''}
        
        # Get directory path without filename
        dir_path = os.path.dirname(original_path)
        
        # Split path into components
        path_parts = []
        while dir_path and dir_path != os.path.dirname(dir_path):
            head, tail = os.path.split(dir_path)
            if tail:
                path_parts.insert(0, tail)
            dir_path = head
        
        # Extract keywords from path
        path_keywords = []
        path_years = []
        for part in path_parts:
            # Normalize: remove special chars, convert to lowercase
            clean_part = re.sub(r'[^\w\s]', ' ', part).lower()
            words = clean_part.split()
            path_keywords.extend(words)
            
            # Extract years from path
            year_matches = re.findall(r'\b(19|20)\d{2}\b', part)
            path_years.extend(year_matches)
        
        # Also extract from filename (without extension)
        filename_base = os.path.splitext(original_filename)[0]
        filename_words = re.sub(r'[^\w\s]', ' ', filename_base).lower().split()
        path_keywords.extend(filename_words)
        
        # Extract years from filename
        year_matches = re.findall(r'\b(19|20)\d{2}\b', filename_base)
        path_years.extend(year_matches)
        
        path_context = ' '.join(path_parts + [filename_base])
        
        return {
            'path_keywords': list(set(path_keywords)),  # Remove duplicates
            'path_years': list(set(path_years)),
            'path_context': path_context.lower()
        }
    
    def _apply_heuristics(self, text: str, filename: str, path_hints: Dict = None) -> Optional[Dict]:
        """Apply heuristic rules to detect common document types."""
        text_lower = text.lower()
        filename_lower = filename.lower()
        combined = text_lower + " " + filename_lower
        
        # Add path hints to combined context
        if path_hints and path_hints.get('path_context'):
            combined += " " + path_hints['path_context']
            path_keywords = set(path_hints.get('path_keywords', []))
        else:
            path_keywords = set()
        
        # Helper function to check path alignment and boost confidence
        def check_match(patterns, workspace, reason, base_boost=2, path_boost_patterns=None):
            """Check if patterns match and calculate confidence boost based on path alignment."""
            if any(term in combined for term in patterns):
                boost = base_boost
                # Additional boost if path contains relevant keywords
                if path_boost_patterns and path_keywords:
                    if any(kw in path_keywords for kw in path_boost_patterns):
                        boost += 1
                        reason += " (path confirms)"
                return {
                    'workspace': workspace,
                    'confidence_boost': boost,
                    'reason': reason
                }
            return None
        
        # Tax documents
        result = check_match(
            ['1040', 'w-2', 'w2', '1099', 'w-9', 'w9', 'tax return', 'irs', 'federal', 'state tax'],
            'KB.Finance.Taxes',
            'Tax form detected',
            base_boost=2,
            path_boost_patterns=['tax', 'taxes', 'irs', 'federal', 'state', 'return']
        )
        if result: return result
        
        # Real estate
        result = check_match(
            ['deed', 'closing disclosure', 'hud-1', 'hud1', 'mortgage', 'property tax', 'escrow'],
            'KB.Assets.RealEstate',
            'Real estate document detected',
            base_boost=2,
            path_boost_patterns=['real', 'estate', 'property', 'house', 'home', 'mortgage', 'deed']
        )
        if result: return result
        
        # Insurance
        result = check_match(
            ['policy', 'insurance', 'life insurance', 'term life', 'disability', 'coverage'],
            'KB.Finance.Insurance',
            'Insurance document detected',
            base_boost=1,
            path_boost_patterns=['insurance', 'policy', 'coverage', 'life', 'health']
        )
        if result: return result
        
        # Identity documents
        result = check_match(
            ['birth certificate', 'passport', 'ssn', 'social security', 'driver', 'license', 'drivers license'],
            'KB.Personal.Identity',
            'Identity document detected',
            base_boost=2,
            path_boost_patterns=['identity', 'id', 'personal', 'passport', 'license', 'ssn']
        )
        if result: return result
        
        # Estate planning
        result = check_match(
            ['will', 'trust', 'power of attorney', 'poa', 'estate plan', 'living will', 'testament'],
            'KB.Personal.Estate',
            'Estate planning document detected',
            base_boost=2,
            path_boost_patterns=['estate', 'will', 'trust', 'legal', 'attorney']
        )
        if result: return result
        
        # Employment
        result = check_match(
            ['employment agreement', 'offer letter', 'employment contract', 'rsu', 'espp', 'w-2', 'w2'],
            'KB.Work.Employment',
            'Employment document detected',
            base_boost=1,
            path_boost_patterns=['work', 'employment', 'job', 'career', 'company', 'employer']
        )
        if result: return result
        
        # Banking
        result = check_match(
            ['bank statement', 'checking', 'savings', 'account statement', 'routing'],
            'KB.Finance.Banking',
            'Banking document detected',
            base_boost=1,
            path_boost_patterns=['bank', 'banking', 'checking', 'savings', 'account', 'chase', 'wells', 'bofa']
        )
        if result: return result
        
        # Investment
        result = check_match(
            ['brokerage', '401k', 'ira', 'investment', 'portfolio', 'k-1', 'k1', 'fidelity', 'vanguard'],
            'KB.Finance.Investments',
            'Investment document detected',
            base_boost=1,
            path_boost_patterns=['investment', 'brokerage', 'portfolio', 'stocks', 'retirement', '401k', 'ira']
        )
        if result: return result
        
        # Health/Medical
        result = check_match(
            ['medical', 'health', 'vaccination', 'doctor', 'hospital', 'prescription', 'eob'],
            'KB.Personal.Health',
            'Health document detected',
            base_boost=1,
            path_boost_patterns=['health', 'medical', 'doctor', 'hospital', 'healthcare']
        )
        if result: return result
        
        # Vehicle documents
        result = check_match(
            ['vehicle', 'auto', 'car', 'registration', 'title', 'dmv'],
            'KB.Assets.Vehicles',
            'Vehicle document detected',
            base_boost=1,
            path_boost_patterns=['vehicle', 'auto', 'car', 'dmv', 'registration', 'title']
        )
        if result: return result
        
        return None
    
    def _extract_metadata(self, text: str, filename: str) -> Dict:
        """Extract metadata hints from text content."""
        metadata = {
            'years': [],
            'amounts': [],
            'institutions': [],
            'form_types': []
        }
        
        # Extract years (4-digit numbers that look like years)
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        metadata['years'] = list(set(years))[-3:]  # Keep up to 3 unique years
        
        # Extract dollar amounts
        amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', text[:2000])
        metadata['amounts'] = amounts[:5]  # Keep first 5
        
        # Extract potential form types (e.g., "Form 1040", "W-2")
        form_patterns = [
            r'Form\s+(\d+\w*)',
            r'\b([W]\-?\d+)\b',
            r'\b(1099[\-\w]*)\b'
        ]
        for pattern in form_patterns:
            forms = re.findall(pattern, text, re.IGNORECASE)
            metadata['form_types'].extend(forms)
        
        return metadata
    
    def _classify_with_llm(self, text: str, filename: str, metadata: Dict, 
                          text_inference, heuristic_hint: Optional[Dict] = None,
                          path_hints: Dict = None) -> Dict:
        """Use LLM to classify the document into a workspace."""
        
        # Truncate text for prompt
        text_snippet = text[:4000] if len(text) > 4000 else text
        
        # Build taxonomy list for prompt
        taxonomy_list = []
        for ws_id, ws_info in self.workspaces.items():
            taxonomy_list.append(f"- {ws_id}: {ws_info['description']}")
        taxonomy_str = "\n".join(taxonomy_list)
        
        # Build metadata context
        metadata_str = ""
        if metadata['years']:
            metadata_str += f"\nYears mentioned: {', '.join(metadata['years'])}"
        if metadata['form_types']:
            metadata_str += f"\nForms detected: {', '.join(metadata['form_types'][:3])}"
        
        # Add path hints if available
        path_str = ""
        if path_hints and path_hints.get('path_context'):
            path_str = f"\nOriginal location: {path_hints['path_context']}"
            if path_hints.get('path_years'):
                path_str += f"\nYears in path: {', '.join(path_hints['path_years'])}"
        
        # Add heuristic hint if available
        hint_str = ""
        if heuristic_hint:
            hint_str = f"\n\nHeuristic hint: {heuristic_hint['reason']} suggests {heuristic_hint['workspace']}"
        
        # Build prompt
        prompt = f"""You are a document classifier for personal financial and legal documents.

Your task: Classify this document into exactly ONE workspace from the taxonomy below.

TAXONOMY (choose one):
{taxonomy_str}

DOCUMENT INFO:
Filename: {filename}{path_str}
{metadata_str}{hint_str}

DOCUMENT EXCERPT:
\"\"\"
{text_snippet}
\"\"\"

Based on the document content, choose the MOST APPROPRIATE workspace.

Also provide:
1. A suggested subfolder path (if applicable, e.g., "Federal/2024" for taxes, or leave empty)
2. A brief 1-sentence description of what this document is
3. A confidence score from 0-5 (0=no confidence, 5=very high confidence)

Respond as JSON (ONLY JSON, no other text):
{{
  "workspace": "KB.Domain.Scope",
  "subpath": "optional/subfolder/path",
  "description": "Brief description",
  "confidence": 4,
  "suggested_name": "brief descriptive name without prefix"
}}"""

        try:
            response = text_inference.create_completion(prompt)
            response_text = response['choices'][0]['text'].strip()
            
            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                import json
                result = json.loads(json_match.group(0))
                
                # Validate workspace exists
                if result['workspace'] not in self.workspaces:
                    result['workspace'] = 'KB.Personal.Misc'
                    result['confidence'] = max(0, result.get('confidence', 2) - 2)
                
                # Apply heuristic confidence boost
                if heuristic_hint and result['workspace'] == heuristic_hint['workspace']:
                    result['confidence'] = min(5, result['confidence'] + heuristic_hint['confidence_boost'])
                
                # Ensure confidence is 0-5 integer
                result['confidence'] = max(0, min(5, int(result.get('confidence', 2))))
                
                return result
            else:
                # Failed to parse, use heuristic or default
                if heuristic_hint:
                    return {
                        'workspace': heuristic_hint['workspace'],
                        'subpath': '',
                        'description': heuristic_hint['reason'],
                        'confidence': 3,
                        'suggested_name': ''
                    }
                else:
                    return {
                        'workspace': 'KB.Personal.Misc',
                        'subpath': '',
                        'description': 'Classification uncertain',
                        'confidence': 1,
                        'suggested_name': ''
                    }
        except Exception as e:
            print(f"LLM classification error: {e}")
            # Fallback to heuristic or misc
            if heuristic_hint:
                return {
                    'workspace': heuristic_hint['workspace'],
                    'subpath': '',
                    'description': heuristic_hint['reason'],
                    'confidence': 3,
                    'suggested_name': ''
                }
            else:
                return {
                    'workspace': 'KB.Personal.Misc',
                    'subpath': '',
                    'description': 'Classification failed',
                    'confidence': 1,
                    'suggested_name': ''
                }
    
    def _generate_filename(self, workspace_config: Dict, metadata: Dict, 
                          original_filename: str, suggested_name: str) -> str:
        """Generate a filename following workspace naming conventions."""
        
        naming = workspace_config.get('naming', {})
        prefix = naming.get('prefix', 'DOC')
        components = naming.get('components', [])
        format_str = naming.get('format', '{prefix}-{doc_type}')
        
        # Build component values
        component_values = {'prefix': prefix}
        
        # Extract year (prefer most recent)
        if 'year' in components or 'date' in components:
            if metadata.get('years'):
                component_values['year'] = metadata['years'][-1]  # Most recent year
            else:
                component_values['year'] = 'Unknown'
        
        # Use suggested name for various components
        clean_name = re.sub(r'[^\w\s]', '', suggested_name).strip()
        clean_name = re.sub(r'\s+', ' ', clean_name)
        words = clean_name.split()[:3]  # Max 3 words
        clean_name = '_'.join(words) if words else 'Document'
        
        # Track which components have been assigned to avoid duplication
        name_parts = words if words else ['Document']
        part_index = 0
        
        # Map common component names
        for comp in components:
            if comp not in component_values:
                if comp in ['doc_type', 'type', 'matter', 'topic']:
                    # Use a specific part of the name or fallback
                    if part_index < len(name_parts):
                        component_values[comp] = name_parts[part_index]
                        part_index += 1
                    else:
                        component_values[comp] = clean_name
                elif comp in ['jurisdiction', 'institution', 'provider', 'employer', 
                             'lender', 'service', 'account', 'property_nickname',
                             'vehicle_name', 'entity_name', 'person', 'ticker_or_topic']:
                    # Use a different part or the first word
                    if part_index < len(name_parts):
                        component_values[comp] = name_parts[part_index]
                        part_index += 1
                    else:
                        component_values[comp] = name_parts[0] if name_parts else 'Unknown'
                elif comp == 'date':
                    if metadata.get('years'):
                        component_values[comp] = metadata['years'][-1]
                    else:
                        component_values[comp] = 'Unknown'
                elif comp == 'period':
                    if metadata.get('years'):
                        component_values[comp] = metadata['years'][-1]
                    else:
                        component_values[comp] = 'Unknown'
                else:
                    component_values[comp] = 'Unknown'
        
        # Format filename
        try:
            filename = format_str.format(**component_values)
        except KeyError:
            # Fallback to simple format
            filename = f"{prefix}-{clean_name}"
        
        # Clean up the filename
        filename = re.sub(r'[^\w\-]', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = re.sub(r'\-+', '-', filename)
        
        return filename

