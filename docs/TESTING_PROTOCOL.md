# Enhanced Automated Testing, Debugging, and Functional Test Protocol

## Overview

This document details an enhanced automated testing and debugging protocol for the **Enhanced File Organizer** project. The protocol incorporates automated functional tests derived from the Product Requirements Document (PRD.md) to ensure code reliability, PRD compliance, and reduce bugs before deployment.

The Enhanced File Organizer is a desktop application with a FastAPI backend (Python 3.12+) and a React/TypeScript frontend, designed to intelligently organize files using local AI models. This testing protocol ensures that all features, from directory scanning to taxonomy-based classification to file migration, meet the requirements specified in the PRD.

## Project Architecture Context

### Technology Stack

**Backend:**
- **Framework**: FastAPI (REST API)
- **Language**: Python 3.12+
- **Database**: SQLite (via `database.py`)
- **AI Models**: Nexa SDK (Llama3.2 3B for text, LLaVA-v1.6 for images)
- **Key Modules**:
  - `backend/api.py` - FastAPI endpoints
  - `backend/classifier.py` - Taxonomy-based classification
  - `backend/database.py` - SQLite persistence
  - `backend/file_utils.py` - File operations
  - `backend/taxonomy.yaml` - Taxonomy structure

**Frontend:**
- **Framework**: React 18.2+ with TypeScript 5.3+
- **Build Tool**: Vite 5.0+
- **UI Framework**: TailwindCSS 3.3+
- **State Management**: TanStack Query 5.8+
- **Table Component**: TanStack Table 8.10+
- **Key Components**:
  - `frontend/src/components/DocumentTable.tsx` - Document listing
  - `frontend/src/components/FileSelector.tsx` - Directory selection
  - `frontend/src/components/PreviewPanel.tsx` - File preview
  - `frontend/src/components/BulkActions.tsx` - Bulk operations

### Application Workflow

The application follows a four-step workflow:
1. **Scan**: Discover files in a directory (`/scan` endpoint)
2. **Classify**: AI-powered classification into taxonomy workspaces (`/classify` endpoint)
3. **Review**: User review and approval of classifications (frontend UI)
4. **Migrate**: Execute file movement to organized structure (`/migrate` endpoint)

## Testing Framework Integration

### Backend Testing Framework

**Primary Framework**: pytest with pytest-asyncio

The backend uses pytest for unit and integration testing, with pytest-asyncio for testing FastAPI's async endpoints.

**Required Dependencies** (add to `requirements.txt`):
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
httpx>=0.25.0  # For testing FastAPI endpoints
```

**Configuration File**: `backend/pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
addopts = 
    --cov=backend
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
    -v
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    functional: Functional tests derived from PRD
    slow: Tests that take longer than 5 seconds
    requires_models: Tests that require AI models to be loaded
```

**Example Test Structure**: `backend/tests/test_api.py`
```python
import pytest
from fastapi.testclient import TestClient
from backend.api import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def sample_file_path(tmp_path):
    """Create a temporary directory with sample files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    (test_dir / "test.txt").write_text("Sample text content")
    (test_dir / "test.pdf").write_bytes(b"PDF content")
    return str(test_dir)

@pytest.mark.integration
def test_scan_directory_endpoint(client, sample_file_path):
    """Test the /scan endpoint (Feature 1)."""
    response = client.post("/api/scan", json={
        "input_path": sample_file_path,
        "output_path": None
    })
    assert response.status_code == 200
    data = response.json()
    assert "file_count" in data
    assert data["file_count"] > 0
    assert "files" in data
```

### Frontend Testing Framework

**Primary Framework**: Vitest with React Testing Library

Vitest is already integrated with Vite, making it the natural choice for frontend testing.

**Required Dependencies** (add to `frontend/package.json` devDependencies):
```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "jsdom": "^23.0.0"
  }
}
```

**Configuration File**: `frontend/vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/dist/'
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
```

**Test Setup File**: `frontend/src/test/setup.ts`
```typescript
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Cleanup after each test
afterEach(() => {
  cleanup();
});
```

**Example Test Structure**: `frontend/src/components/__tests__/DocumentTable.test.tsx`
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import DocumentTable from '../DocumentTable';
import { DocumentItem } from '../../types';

describe('DocumentTable', () => {
  const mockItems: DocumentItem[] = [
    {
      id: '1',
      source_path: '/test/file1.txt',
      original_filename: 'file1.txt',
      proposed_workspace: 'KB.Work.Projects',
      proposed_subpath: '2024',
      proposed_filename: 'Project_File_2024.txt',
      confidence: 4,
      status: 'pending',
      extracted_text: 'Sample content',
      description: 'Test file'
    }
  ];

  it('renders document table with items', () => {
    render(
      <DocumentTable
        items={mockItems}
        selectedIds={new Set()}
        onSelectionChange={vi.fn()}
        onItemClick={vi.fn()}
        onItemUpdate={vi.fn()}
      />
    );
    
    expect(screen.getByText('file1.txt')).toBeInTheDocument();
    expect(screen.getByText('KB.Work.Projects')).toBeInTheDocument();
  });
});
```

## Automated Test Execution and Triggering

### IDE Integration

The testing protocol integrates with the IDE to automatically execute tests upon code changes. This is achieved through:

1. **File Watchers**: Monitor source files and trigger tests on save
2. **Pre-commit Hooks**: Run tests before allowing commits
3. **CI/CD Pipeline**: Execute full test suite on push/PR

### Trigger Events

Tests are automatically triggered on:

- **File Save**: When a developer saves a file, relevant tests are run
- **Git Commit**: Pre-commit hook runs tests before commit
- **Pull Request**: CI/CD pipeline runs full test suite
- **PRD Update**: When PRD.md is modified, functional tests are regenerated
- **Scheduled Intervals**: Nightly full test suite execution

### Pre-commit Hook Configuration

**File**: `.pre-commit-config.yaml`
```yaml
repos:
  - repo: local
    hooks:
      - id: backend-tests
        name: Backend Tests
        entry: bash -c 'cd backend && python -m pytest tests/ -v --tb=short'
        language: system
        pass_filenames: false
        always_run: true
        
      - id: frontend-tests
        name: Frontend Tests
        entry: bash -c 'cd frontend && npm run test:ci'
        language: system
        pass_filenames: false
        always_run: true
        
      - id: lint-backend
        name: Lint Backend
        entry: bash -c 'cd backend && python -m flake8 . --max-line-length=120'
        language: system
        pass_filenames: true
        types: [python]
```

**Installation**:
```bash
pip install pre-commit
pre-commit install
```

### File Watcher Configuration

For VS Code, create `.vscode/settings.json`:
```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "backend/tests",
    "-v",
    "--tb=short"
  ],
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  "vitest.enable": true,
  "vitest.commandLine": "npm run test",
  "vitest.include": ["frontend/src/**/*.{test,spec}.{js,ts,jsx,tsx}"]
}
```

## Functional Test Generation and Execution from PRD

### PRD Parser Implementation

A PRD parser extracts requirements, features, and acceptance criteria from `PRD.md` and generates executable test cases.

**File**: `backend/tests/prd_parser.py`
```python
"""
Parser for extracting test requirements from PRD.md.
"""
import re
import yaml
from typing import List, Dict, Any
from pathlib import Path

class PRDParser:
    """Parse PRD.md to extract testable requirements."""
    
    def __init__(self, prd_path: str):
        """Initialize parser with PRD file path."""
        self.prd_path = Path(prd_path)
        self.content = self._load_prd()
        
    def _load_prd(self) -> str:
        """Load PRD content."""
        with open(self.prd_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_features(self) -> List[Dict[str, Any]]:
        """Extract all features from PRD."""
        features = []
        feature_pattern = r'### Feature (\d+): (.+?)\n\n\*\*Description\*\*: (.+?)\n\n\*\*Functionality\*\*:\n((?:\* .+?\n)+)'
        
        matches = re.finditer(feature_pattern, self.content, re.DOTALL)
        for match in matches:
            feature_num = match.group(1)
            feature_name = match.group(2)
            description = match.group(3)
            functionality = match.group(4)
            
            # Extract functionality items
            func_items = re.findall(r'\* (.+?)(?=\n\*|\n\n|$)', functionality, re.DOTALL)
            
            features.append({
                'number': int(feature_num),
                'name': feature_name,
                'description': description,
                'functionality': func_items
            })
        
        return features
    
    def extract_goals(self) -> List[Dict[str, Any]]:
        """Extract goals and measurable targets."""
        goals = []
        goal_pattern = r'### Goal (\d+): (.+?)\n\n\*\*Objective\*\*: (.+?)\n\n\*\*Measurable Targets\*\*:\n((?:\* .+?\n)+)'
        
        matches = re.finditer(goal_pattern, self.content, re.DOTALL)
        for match in matches:
            goal_num = match.group(1)
            goal_name = match.group(2)
            objective = match.group(3)
            targets = match.group(4)
            
            target_items = re.findall(r'\* (.+?)(?=\n\*|\n\n|$)', targets, re.DOTALL)
            
            goals.append({
                'number': int(goal_num),
                'name': goal_name,
                'objective': objective,
                'targets': target_items
            })
        
        return goals
    
    def generate_test_cases(self) -> List[Dict[str, Any]]:
        """Generate test cases from PRD features."""
        features = self.extract_features()
        test_cases = []
        
        for feature in features:
            # Generate test cases for each feature
            test_cases.extend(self._generate_feature_tests(feature))
        
        return test_cases
    
    def _generate_feature_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test cases for a specific feature."""
        tests = []
        feature_num = feature['number']
        feature_name = feature['name']
        
        # Map features to test templates
        test_templates = {
            1: self._generate_scan_tests,  # Directory Scanning
            2: self._generate_classification_tests,  # AI-Powered Classification
            3: self._generate_review_tests,  # Review Workflow
            4: self._generate_bulk_action_tests,  # Bulk Actions
            5: self._generate_preview_tests,  # File Preview
            6: self._generate_migration_tests,  # Migration
            9: self._generate_taxonomy_tests,  # Taxonomy Management
            10: self._generate_misc_tests,  # Misc/No Good Fit
            11: self._generate_database_tests,  # Database Persistence
            12: self._generate_power_user_tests  # Power User Mode
        }
        
        if feature_num in test_templates:
            tests = test_templates[feature_num](feature)
        
        return tests
    
    def _generate_scan_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 1: Directory Scanning."""
        return [
            {
                'name': f"test_scan_recursive_directory",
                'description': 'Test recursive directory scanning',
                'gherkin': '''
Given a directory with nested subdirectories
When I call the /scan endpoint
Then all supported files in nested folders should be discovered
                ''',
                'test_type': 'integration',
                'feature': 'Feature 1'
            },
            {
                'name': f"test_scan_file_type_filtering",
                'description': 'Test file type filtering',
                'gherkin': '''
Given a directory with supported and unsupported files
When I call the /scan endpoint
Then only supported file types should be returned
                ''',
                'test_type': 'integration',
                'feature': 'Feature 1'
            },
            {
                'name': f"test_scan_metadata_extraction",
                'description': 'Test metadata extraction',
                'gherkin': '''
Given a scanned file
When I retrieve file information
Then metadata should include size, extension, and modification date
                ''',
                'test_type': 'unit',
                'feature': 'Feature 1'
            }
        ]
    
    def _generate_classification_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 2: AI-Powered Classification."""
        return [
            {
                'name': 'test_classify_text_document',
                'description': 'Test classification of text documents',
                'gherkin': '''
Given a text document (TXT, DOCX, MD, PDF)
When I classify the file
Then it should be assigned to a KB.<Domain>.<Scope> workspace
And a descriptive filename should be generated
                ''',
                'test_type': 'functional',
                'feature': 'Feature 2',
                'requires_models': True
            },
            {
                'name': 'test_classify_image_file',
                'description': 'Test classification of image files',
                'gherkin': '''
Given an image file (PNG, JPG, JPEG, GIF, BMP)
When I classify the file using vision-language model
Then it should be assigned to an appropriate workspace
And a descriptive filename should be generated
                ''',
                'test_type': 'functional',
                'feature': 'Feature 2',
                'requires_models': True
            },
            {
                'name': 'test_classify_taxonomy_format',
                'description': 'Test taxonomy format compliance',
                'gherkin': '''
Given a classified file
When I check the proposed workspace
Then it should follow KB.<Domain>.<Scope> format
And the workspace should exist in taxonomy.yaml
                ''',
                'test_type': 'unit',
                'feature': 'Feature 2'
            },
            {
                'name': 'test_classify_confidence_scoring',
                'description': 'Test confidence score generation',
                'gherkin': '''
Given a classified file
When I check the confidence score
Then it should be between 0 and 5
And low confidence items should be flagged
                ''',
                'test_type': 'unit',
                'feature': 'Feature 2'
            }
        ]
    
    def _generate_review_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 3: Review Workflow."""
        return [
            {
                'name': 'test_review_table_display',
                'description': 'Test document table display',
                'gherkin': '''
Given classified files
When I view the review table
Then all files should be displayed with proposed classifications
And confidence indicators should be visible
                ''',
                'test_type': 'integration',
                'feature': 'Feature 3'
            },
            {
                'name': 'test_review_edit_classification',
                'description': 'Test editing classifications',
                'gherkin': '''
Given a file in review
When I edit the workspace, subpath, or filename
Then the changes should be saved to the database
And the UI should reflect the updated values
                ''',
                'test_type': 'integration',
                'feature': 'Feature 3'
            },
            {
                'name': 'test_review_approve_reject',
                'description': 'Test approve/reject actions',
                'gherkin': '''
Given a file in review
When I approve or reject the classification
Then the status should be updated in the database
And the item should be marked as approved or rejected
                ''',
                'test_type': 'integration',
                'feature': 'Feature 3'
            }
        ]
    
    def _generate_bulk_action_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 4: Bulk Actions."""
        return [
            {
                'name': 'test_bulk_approve',
                'description': 'Test bulk approval',
                'gherkin': '''
Given multiple selected files
When I perform bulk approve
Then all selected files should be marked as approved
                ''',
                'test_type': 'integration',
                'feature': 'Feature 4'
            },
            {
                'name': 'test_bulk_workspace_assignment',
                'description': 'Test bulk workspace assignment',
                'gherkin': '''
Given multiple selected files
When I assign a workspace to all selected
Then all selected files should have the new workspace
                ''',
                'test_type': 'integration',
                'feature': 'Feature 4'
            }
        ]
    
    def _generate_preview_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 5: File Preview."""
        return [
            {
                'name': 'test_preview_text_content',
                'description': 'Test text content preview',
                'gherkin': '''
Given a text file
When I click to preview
Then extracted text content should be displayed
                ''',
                'test_type': 'integration',
                'feature': 'Feature 5'
            },
            {
                'name': 'test_preview_image',
                'description': 'Test image preview',
                'gherkin': '''
Given an image file
When I click to preview
Then the image should be displayed with zoom capability
                ''',
                'test_type': 'integration',
                'feature': 'Feature 5'
            }
        ]
    
    def _generate_migration_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 6: Migration."""
        return [
            {
                'name': 'test_migration_create_structure',
                'description': 'Test directory structure creation',
                'gherkin': '''
Given approved classifications
When I execute migration
Then the directory structure should be created according to taxonomy
                ''',
                'test_type': 'integration',
                'feature': 'Feature 6'
            },
            {
                'name': 'test_migration_file_movement',
                'description': 'Test file movement',
                'gherkin': '''
Given approved classifications
When I execute migration
Then files should be moved to correct destinations
And original files should be preserved or copied based on preference
                ''',
                'test_type': 'integration',
                'feature': 'Feature 6'
            },
            {
                'name': 'test_migration_conflict_handling',
                'description': 'Test filename conflict handling',
                'gherkin': '''
Given files with duplicate proposed filenames
When I execute migration
Then conflicts should be resolved with unique filenames
                ''',
                'test_type': 'integration',
                'feature': 'Feature 6'
            }
        ]
    
    def _generate_taxonomy_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 9: Taxonomy Management."""
        return [
            {
                'name': 'test_taxonomy_validation',
                'description': 'Test taxonomy structure validation',
                'gherkin': '''
Given a taxonomy.yaml file
When I validate the taxonomy
Then it should conform to four-level spine structure
And all workspaces should have required fields
                ''',
                'test_type': 'unit',
                'feature': 'Feature 9'
            },
            {
                'name': 'test_taxonomy_workspace_selector',
                'description': 'Test workspace selector',
                'gherkin': '''
Given the taxonomy structure
When I view the workspace selector
Then all KB.<Domain>.<Scope> workspaces should be available
And descriptions should be displayed
                ''',
                'test_type': 'integration',
                'feature': 'Feature 9'
            }
        ]
    
    def _generate_misc_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 10: Misc/No Good Fit."""
        return [
            {
                'name': 'test_misc_classification',
                'description': 'Test Misc classification',
                'gherkin': '''
Given a file that cannot be classified
When classification is performed
Then it should be assigned to Misc or no_good_fit
                ''',
                'test_type': 'functional',
                'feature': 'Feature 10'
            },
            {
                'name': 'test_misc_review_view',
                'description': 'Test Misc items review',
                'gherkin': '''
Given files classified as Misc
When I view the Misc filter
Then all Misc items should be displayed
And I should be able to reassign them
                ''',
                'test_type': 'integration',
                'feature': 'Feature 10'
            }
        ]
    
    def _generate_database_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 11: Database Persistence."""
        return [
            {
                'name': 'test_database_persistence',
                'description': 'Test session persistence',
                'gherkin': '''
Given scanned and classified files
When I restart the application
Then all items should be restored from database
And status should be preserved
                ''',
                'test_type': 'integration',
                'feature': 'Feature 11'
            },
            {
                'name': 'test_database_migration_history',
                'description': 'Test migration history tracking',
                'gherkin': '''
Given migrated files
When I check migration history
Then all migrations should be recorded with timestamps
                ''',
                'test_type': 'integration',
                'feature': 'Feature 11'
            }
        ]
    
    def _generate_power_user_tests(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tests for Feature 12: Power User Mode."""
        return [
            {
                'name': 'test_power_user_mode_toggle',
                'description': 'Test power user mode activation',
                'gherkin': '''
Given power user mode toggle
When I enable power user mode
Then debug features should be available
And taxonomy management tools should be accessible
                ''',
                'test_type': 'integration',
                'feature': 'Feature 12'
            },
            {
                'name': 'test_debug_llm_prompt_viewing',
                'description': 'Test LLM prompt/response viewing',
                'gherkin': '''
Given power user mode enabled
When I view a classified file
Then LLM prompt and response should be visible in debug section
                ''',
                'test_type': 'integration',
                'feature': 'Feature 12'
            }
        ]
```

### BDD Test Execution

Generated Gherkin scenarios are converted to executable pytest tests using pytest-bdd.

**File**: `backend/tests/conftest.py`
```python
"""
Pytest configuration and fixtures for BDD tests.
"""
import pytest
from pathlib import Path
from backend.tests.prd_parser import PRDParser

# Load PRD and generate test cases
PRD_PATH = Path(__file__).parent.parent.parent / "PRD.md"
prd_parser = PRDParser(str(PRD_PATH))
test_cases = prd_parser.generate_test_cases()

@pytest.fixture(scope="session")
def prd_test_cases():
    """Provide PRD-generated test cases."""
    return test_cases

@pytest.fixture
def test_database(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    # Initialize test database
    from backend.database import Database
    db = Database(str(db_path))
    yield db
    db.close()
```

**Example BDD Test**: `backend/tests/functional/test_classification_bdd.py`
```python
"""
BDD tests for Feature 2: AI-Powered Classification.
Generated from PRD.md.
"""
import pytest
from pytest_bdd import given, when, then, scenario
from pathlib import Path
import tempfile
import shutil

from backend.classifier import TaxonomyClassifier
from backend.file_utils import read_file_data

# Load scenarios from PRD parser
from backend.tests.prd_parser import PRDParser

PRD_PATH = Path(__file__).parent.parent.parent.parent / "PRD.md"
parser = PRDParser(str(PRD_PATH))
classification_tests = [tc for tc in parser.generate_test_cases() 
                       if tc['feature'] == 'Feature 2']

@pytest.mark.functional
@pytest.mark.requires_models
@scenario('test_classify_text_document', 'Classify text document')
def test_classify_text_document_scenario():
    """Test classification of text documents."""
    pass

@given("a text document (TXT, DOCX, MD, PDF)")
def create_text_document(tmp_path):
    """Create a sample text document."""
    test_file = tmp_path / "test_document.txt"
    test_file.write_text("This is a project proposal for Q4 2024.")
    return str(test_file)

@when("I classify the file")
def classify_file(create_text_document, test_database):
    """Classify the text document."""
    file_path = create_text_document
    taxonomy_path = Path(__file__).parent.parent.parent / "backend" / "taxonomy.yaml"
    classifier = TaxonomyClassifier(str(taxonomy_path))
    
    text_content = read_file_data(file_path)
    result = classifier.classify(
        extracted_text=text_content,
        original_filename=Path(file_path).name,
        text_inference=None,  # Mock in actual test
        original_path=file_path
    )
    
    return result

@then("it should be assigned to a KB.<Domain>.<Scope> workspace")
def verify_workspace_format(classify_file):
    """Verify workspace follows taxonomy format."""
    result = classify_file
    workspace = result['workspace']
    assert workspace.startswith('KB.'), f"Workspace {workspace} does not start with KB."
    parts = workspace.split('.')
    assert len(parts) == 3, f"Workspace {workspace} does not follow KB.<Domain>.<Scope> format"
    assert parts[0] == 'KB'
    
@then("a descriptive filename should be generated")
def verify_filename(classify_file):
    """Verify descriptive filename is generated."""
    result = classify_file
    assert 'filename' in result
    assert result['filename'] != Path(result.get('original_path', '')).name
    assert len(result['filename']) > 0
```

## Bug Identification and Reporting

### Stack Trace Analysis

When a test fails, the IDE automatically analyzes the stack trace to identify the source of the bug.

**File**: `backend/tests/bug_analyzer.py`
```python
"""
Bug analysis and reporting from test failures.
"""
import re
import traceback
from typing import Dict, List, Optional
from pathlib import Path

class BugAnalyzer:
    """Analyze test failures and identify bug sources."""
    
    def analyze_failure(self, test_name: str, error: Exception, 
                       traceback_str: str) -> Dict:
        """Analyze a test failure and generate bug report."""
        stack_trace = self._parse_stack_trace(traceback_str)
        bug_location = self._identify_bug_location(stack_trace)
        bug_type = self._classify_bug_type(error, stack_trace)
        suggestions = self._generate_fix_suggestions(bug_type, bug_location)
        
        # Map to PRD requirement
        prd_requirement = self._map_to_prd_requirement(test_name)
        
        return {
            'test_name': test_name,
            'bug_description': str(error),
            'bug_type': bug_type,
            'file': bug_location['file'],
            'line': bug_location['line'],
            'function': bug_location['function'],
            'stack_trace': stack_trace,
            'fix_suggestions': suggestions,
            'prd_requirement': prd_requirement
        }
    
    def _parse_stack_trace(self, traceback_str: str) -> List[Dict]:
        """Parse stack trace into structured format."""
        lines = traceback_str.split('\n')
        frames = []
        
        for i, line in enumerate(lines):
            if 'File "' in line:
                file_match = re.search(r'File "([^"]+)", line (\d+)', line)
                if file_match:
                    func_line = lines[i+1] if i+1 < len(lines) else ""
                    func_match = re.search(r'in (\w+)', func_line)
                    
                    frames.append({
                        'file': file_match.group(1),
                        'line': int(file_match.group(2)),
                        'function': func_match.group(1) if func_match else 'unknown'
                    })
        
        return frames
    
    def _identify_bug_location(self, stack_trace: List[Dict]) -> Dict:
        """Identify the most likely bug location from stack trace."""
        # Prioritize application code over test code
        for frame in stack_trace:
            if 'backend/' in frame['file'] and 'test' not in frame['file']:
                return frame
        
        # Fallback to first frame
        return stack_trace[0] if stack_trace else {'file': 'unknown', 'line': 0, 'function': 'unknown'}
    
    def _classify_bug_type(self, error: Exception, stack_trace: List[Dict]) -> str:
        """Classify the type of bug."""
        error_type = type(error).__name__
        error_msg = str(error)
        
        if 'AttributeError' in error_type:
            return 'missing_attribute'
        elif 'KeyError' in error_type:
            return 'missing_key'
        elif 'TypeError' in error_type:
            return 'type_mismatch'
        elif 'ValueError' in error_type:
            return 'invalid_value'
        elif 'AssertionError' in error_type:
            return 'assertion_failure'
        elif 'HTTPException' in error_type or '404' in error_msg:
            return 'endpoint_error'
        else:
            return 'unknown'
    
    def _generate_fix_suggestions(self, bug_type: str, location: Dict) -> List[str]:
        """Generate fix suggestions based on bug type."""
        suggestions = {
            'missing_attribute': [
                f"Check if attribute exists in {location['function']}",
                "Add null check before accessing attribute",
                "Verify object initialization"
            ],
            'missing_key': [
                "Check dictionary key existence before access",
                "Use .get() method with default value",
                "Verify data structure matches expected format"
            ],
            'type_mismatch': [
                "Verify variable types match expected types",
                "Add type conversion if needed",
                "Check function parameter types"
            ],
            'invalid_value': [
                "Add input validation",
                "Check value ranges and constraints",
                "Verify data format"
            ],
            'assertion_failure': [
                "Review test expectations",
                "Check actual vs expected values",
                "Verify test data setup"
            ],
            'endpoint_error': [
                "Check endpoint route definition",
                "Verify request/response models",
                "Check authentication/authorization"
            ]
        }
        
        return suggestions.get(bug_type, ["Review error and stack trace for details"])
    
    def _map_to_prd_requirement(self, test_name: str) -> Optional[str]:
        """Map test name to PRD requirement."""
        # Extract feature number from test name
        feature_match = re.search(r'feature[_\s]*(\d+)', test_name, re.IGNORECASE)
        if feature_match:
            feature_num = feature_match.group(1)
            return f"Feature {feature_num}"
        
        return None
```

### Code Coverage Analysis

Code coverage analysis identifies untested code paths that may contain bugs.

**Coverage Configuration**: `backend/.coveragerc`
```ini
[run]
source = backend
omit = 
    */tests/*
    */__pycache__/*
    */venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

**Coverage Report Integration**: Tests automatically generate coverage reports, and the IDE highlights uncovered lines.

### PRD Requirement Tracing

Each test failure is traced back to the specific PRD requirement it validates.

**File**: `backend/tests/test_tracker.py`
```python
"""
Track test-to-PRD requirement mapping.
"""
from typing import Dict, List
from backend.tests.prd_parser import PRDParser

class PRDTestTracker:
    """Track which tests validate which PRD requirements."""
    
    def __init__(self, prd_path: str):
        self.parser = PRDParser(prd_path)
        self.test_mapping = self._build_mapping()
    
    def _build_mapping(self) -> Dict[str, List[str]]:
        """Build mapping from PRD features to test names."""
        mapping = {}
        test_cases = self.parser.generate_test_cases()
        
        for test_case in test_cases:
            feature = test_case['feature']
            if feature not in mapping:
                mapping[feature] = []
            mapping[feature].append(test_case['name'])
        
        return mapping
    
    def get_requirement_for_test(self, test_name: str) -> str:
        """Get PRD requirement for a test."""
        for feature, tests in self.test_mapping.items():
            if test_name in tests:
                return feature
        return "Unknown"
```

## Automated Bug Fixing

### Pattern-Based Fixes

Common bug patterns are automatically fixed using predefined transformations.

**File**: `backend/tests/auto_fix.py`
```python
"""
Automated bug fixing based on common patterns.
"""
import ast
import re
from typing import Dict, List

class AutoFixer:
    """Automatically fix common bug patterns."""
    
    def fix_missing_attribute(self, code: str, attribute: str, 
                              context: Dict) -> str:
        """Fix missing attribute errors."""
        # Add null check
        pattern = rf'(\w+)\.{attribute}'
        replacement = rf'\1.{attribute} if \1 and hasattr(\1, "{attribute}") else None'
        return re.sub(pattern, replacement, code)
    
    def fix_missing_key(self, code: str, key: str) -> str:
        """Fix missing dictionary key errors."""
        # Replace dict[key] with dict.get(key, default)
        pattern = rf'(\w+)\[{re.escape(key)}\]'
        replacement = rf'\1.get("{key}", None)'
        return re.sub(pattern, replacement, code)
    
    def fix_type_mismatch(self, code: str, expected_type: str) -> str:
        """Fix type mismatch errors."""
        # Add type conversion
        if expected_type == 'int':
            return f"int({code})"
        elif expected_type == 'str':
            return f"str({code})"
        return code
```

### AI-Powered Fix Suggestions

The IDE uses AI to suggest fixes based on error context and code patterns.

**Integration**: The bug analyzer generates fix suggestions that are presented to the developer for review before application.

## CI/CD Integration

### GitHub Actions Workflow

**File**: `.github/workflows/test.yml`
```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
    
    - name: Run backend tests
      run: |
        cd backend
        pytest tests/ -v --cov=backend --cov-report=xml --cov-report=html
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run frontend tests
      run: |
        cd frontend
        npm run test:ci
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info
        flags: frontend
  
  functional-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.12"
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-bdd
    
    - name: Generate functional tests from PRD
      run: |
        python -m backend.tests.prd_parser --generate-tests
    
    - name: Run functional tests
      run: |
        cd backend
        pytest tests/functional/ -v -m functional
```

**Frontend Test Script**: Add to `frontend/package.json`
```json
{
  "scripts": {
    "test": "vitest",
    "test:ci": "vitest run --coverage",
    "test:ui": "vitest --ui"
  }
}
```

## Example Scenario: End-to-End Testing Workflow

### Scenario: Developer Implements Classification Feature

1. **Developer modifies** `backend/classifier.py` to add a new classification rule.

2. **IDE automatically triggers** tests:
   - Unit tests for `TaxonomyClassifier` class
   - Integration tests for `/classify` endpoint
   - Functional tests for Feature 2 (AI-Powered Classification)

3. **A functional test fails**: `test_classify_taxonomy_format` fails because the new rule generates a workspace that doesn't follow `KB.<Domain>.<Scope>` format.

4. **Bug analyzer identifies**:
   - **File**: `backend/classifier.py`
   - **Line**: 145
   - **Function**: `_classify_with_llm`
   - **Bug Type**: `invalid_value`
   - **PRD Requirement**: Feature 2 - AI-Powered Taxonomy-Based Classification
   - **Fix Suggestions**:
     - Validate workspace format before returning
     - Ensure workspace matches taxonomy.yaml entries
     - Add format validation function

5. **Developer reviews** the fix suggestions and applies the validation fix.

6. **IDE re-runs** tests automatically.

7. **All tests pass**, including:
   - Unit tests: 45/45 passed
   - Integration tests: 12/12 passed
   - Functional tests: 8/8 passed
   - Code coverage: 82% (above 80% target)

8. **IDE marks code as ready** and compliant with PRD Feature 2 requirements.

## Success Metrics

The testing protocol aims to achieve the following metrics, aligned with PRD goals:

### Code Quality Metrics

- **Code Coverage**: Target 80%+ (as specified in PRD Release Criteria)
  - Current baseline: 0% (no tests currently)
  - Measurement: pytest-cov and @vitest/coverage-v8 reports

- **Test Execution Time**: 
  - Unit tests: < 30 seconds
  - Integration tests: < 2 minutes
  - Full test suite: < 5 minutes

### PRD Compliance Metrics

- **Functional Test Coverage**: 95%+ of PRD features have automated tests
  - Measurement: Count of PRD features with corresponding test cases
  - Target: All 12 features have functional tests

- **Requirement Traceability**: 100% of functional tests mapped to PRD requirements
  - Measurement: Test-to-requirement mapping coverage

### Bug Reduction Metrics

- **Production Bugs**: Target 30% reduction [Illustrative]
  - Baseline: Track bugs in production
  - Measurement: Compare pre/post implementation bug counts

- **Debugging Time**: Target 15% reduction [Illustrative]
  - Measurement: Time from bug detection to fix
  - Track via issue resolution times

### Test Reliability Metrics

- **Test Stability**: < 5% flaky test rate
  - Measurement: Tests that pass/fail inconsistently
  - Target: All tests should be deterministic

- **CI/CD Success Rate**: > 95% of builds pass
  - Measurement: Successful CI runs / Total CI runs

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

1. **Set up testing frameworks**
   - Install pytest and dependencies
   - Configure Vitest for frontend
   - Set up coverage reporting

2. **Create test infrastructure**
   - Create `backend/tests/` directory structure
   - Create `frontend/src/__tests__/` directory structure
   - Set up test fixtures and utilities

3. **Implement basic tests**
   - Unit tests for core utilities (`file_utils.py`, `database.py`)
   - Integration tests for API endpoints
   - Component tests for React components

### Phase 2: PRD Parser and Functional Tests (Weeks 3-4)

1. **Implement PRD parser**
   - Create `prd_parser.py` module
   - Extract features and requirements from PRD.md
   - Generate test case templates

2. **Implement BDD test framework**
   - Set up pytest-bdd
   - Convert Gherkin scenarios to executable tests
   - Create step definitions

3. **Generate functional tests**
   - Generate tests for all 12 PRD features
   - Implement test data fixtures
   - Set up mock AI models for testing

### Phase 3: Bug Analysis and Auto-Fix (Weeks 4-5)

1. **Implement bug analyzer**
   - Stack trace parsing
   - Bug type classification
   - PRD requirement mapping

2. **Implement auto-fix system**
   - Pattern-based fixes
   - Fix suggestion generation
   - Preview and approval workflow

3. **IDE integration**
   - File watcher configuration
   - Pre-commit hooks
   - Test result display

### Phase 4: CI/CD Integration (Week 6)

1. **Set up GitHub Actions**
   - Backend test workflow
   - Frontend test workflow
   - Functional test workflow
   - Coverage reporting

2. **Configure code quality gates**
   - Coverage thresholds
   - Test failure blocking
   - PRD compliance checks

### Phase 5: Documentation and Rollout (Week 7)

1. **Documentation**
   - Update README with testing instructions
   - Create testing guide for developers
   - Document PRD-to-test mapping

2. **Team rollout**
   - Training session on testing protocol
   - Demo of automated testing workflow
   - Gather feedback and iterate

## Conclusion

This enhanced automated testing, debugging, and functional test protocol provides a comprehensive framework for ensuring code quality and PRD compliance in the Enhanced File Organizer project. By automatically generating functional tests from the PRD, identifying bugs through intelligent analysis, and providing automated fix suggestions, the protocol significantly reduces debugging time and improves code reliability.

The integration of pytest for backend testing, Vitest for frontend testing, and BDD-style functional tests derived from PRD requirements ensures that all features meet their specified requirements before deployment. The CI/CD integration provides continuous validation, and the bug analysis system helps developers quickly identify and resolve issues.

Through this protocol, the Enhanced File Organizer project aims to achieve:
- 80%+ code coverage
- 95%+ PRD compliance via functional tests
- 30% reduction in production bugs
- 15% reduction in debugging time

This results in more reliable software, faster development cycles, and higher confidence in deployments.

