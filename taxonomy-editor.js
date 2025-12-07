/**
 * Taxonomy Editor - Main JavaScript
 * Handles loading, editing, and exporting taxonomy data
 */

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

const state = {
    taxonomy: null,
    originalYaml: null,
    selectedNode: null,
    hasUnsavedChanges: false,
    expandedNodes: new Set(['KB']) // Root is expanded by default
};

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    attachEventListeners();
});

async function initializeApp() {
    try {
        // Load taxonomy from YAML file
        const response = await fetch('backend/taxonomy.yaml');
        const yamlText = await response.text();
        state.originalYaml = yamlText;
        state.taxonomy = jsyaml.load(yamlText);

        // Render the tree
        renderTree();

        console.log('Taxonomy loaded successfully');
    } catch (error) {
        console.error('Error loading taxonomy:', error);
        showNotification('Error loading taxonomy.yaml', 'error');
    }
}

// =============================================================================
// EVENT LISTENERS
// =============================================================================

function attachEventListeners() {
    // Header buttons
    document.getElementById('saveBtn').addEventListener('click', saveTaxonomy);
    document.getElementById('discardBtn').addEventListener('click', discardChanges);
    document.getElementById('exportBtn').addEventListener('click', exportYaml);
    document.getElementById('validateBtn').addEventListener('click', validateTaxonomy);

    // Sidebar
    document.getElementById('searchBox').addEventListener('input', handleSearch);
    document.getElementById('addDomainBtn').addEventListener('click', () => showAddModal('domain'));

    // Details panel
    document.getElementById('editTitleBtn').addEventListener('click', editNodeTitle);
    document.getElementById('deleteScopeBtn').addEventListener('click', deleteNode);
    document.getElementById('addScopeBtn').addEventListener('click', () => showAddModal('scope'));
    document.getElementById('addExampleBtn').addEventListener('click', addExample);

    // Form inputs - track changes
    const formInputs = [
        'descriptionInput',
        'decisionsInput',
        'llmContextInput',
        'prefixInput',
        'formatInput',
        'componentsInput'
    ];

    formInputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', () => {
                if (state.selectedNode) {
                    updateSelectedNode();
                }
            });
        }
    });

    // Modal
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modal').addEventListener('click', (e) => {
        if (e.target.id === 'modal') {
            closeModal();
        }
    });
}

// =============================================================================
// TREE RENDERING
// =============================================================================

function renderTree() {
    const treeContainer = document.getElementById('treeContainer');
    treeContainer.innerHTML = '';

    if (!state.taxonomy || !state.taxonomy.workspaces) {
        treeContainer.innerHTML = '<div class="empty-state"><p>No taxonomy data available</p></div>';
        return;
    }

    // Create root node
    const rootNode = createTreeNode('KB', 'KB', 'namespace', 0, null);
    treeContainer.appendChild(rootNode);

    // Group workspaces by domain
    const domainMap = groupByDomain(state.taxonomy.workspaces);

    // Create domain nodes
    const rootChildren = rootNode.querySelector('.tree-children');
    Object.keys(domainMap).sort().forEach(domainName => {
        const domainNode = createTreeNode(
            `KB.${domainName}`,
            domainName,
            'domain',
            1,
            domainMap[domainName]
        );
        rootChildren.appendChild(domainNode);
    });
}

function groupByDomain(workspaces) {
    const domainMap = {};

    workspaces.forEach(workspace => {
        const parts = workspace.id.split('.');
        if (parts.length >= 2) {
            const domain = parts[1];
            if (!domainMap[domain]) {
                domainMap[domain] = [];
            }
            domainMap[domain].push(workspace);
        }
    });

    return domainMap;
}

function createTreeNode(fullId, label, type, level, children = null) {
    const node = document.createElement('div');
    node.className = 'tree-node';
    node.dataset.id = fullId;
    node.dataset.type = type;

    const hasChildren = children && children.length > 0;
    const isExpanded = state.expandedNodes.has(fullId);

    // Create header
    const header = document.createElement('div');
    header.className = 'tree-node-header';
    if (state.selectedNode === fullId) {
        header.classList.add('active');
    }

    // Expand icon
    const expandIcon = createSvg('chevron-right', 'tree-expand-icon');
    if (hasChildren || type === 'domain') {
        if (isExpanded) {
            expandIcon.classList.add('expanded');
        }
        expandIcon.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleNode(fullId);
        });
    } else {
        expandIcon.classList.add('hidden');
    }
    header.appendChild(expandIcon);

    // Node icon
    const icon = createSvg(type === 'domain' ? 'folder' : 'file', `tree-node-icon ${type}`);
    header.appendChild(icon);

    // Label
    const labelSpan = document.createElement('span');
    labelSpan.className = 'tree-node-label';
    labelSpan.textContent = label;
    header.appendChild(labelSpan);

    // Count badge for domains
    if (type === 'domain' && hasChildren) {
        const count = document.createElement('span');
        count.className = 'tree-node-count';
        count.textContent = children.length;
        header.appendChild(count);
    }

    // Click handler for selection
    header.addEventListener('click', () => selectNode(fullId, type, children));

    node.appendChild(header);

    // Children container
    const childrenContainer = document.createElement('div');
    childrenContainer.className = `tree-children ${isExpanded ? '' : 'collapsed'}`;

    if (type === 'domain' && children) {
        children.sort((a, b) => {
            const aName = a.id.split('.').pop();
            const bName = b.id.split('.').pop();
            return aName.localeCompare(bName);
        }).forEach(workspace => {
            const scopeNode = createTreeNode(
                workspace.id,
                workspace.id.split('.').pop(),
                'scope',
                level + 1,
                null
            );
            childrenContainer.appendChild(scopeNode);
        });
    }

    node.appendChild(childrenContainer);

    return node;
}

function toggleNode(nodeId) {
    if (state.expandedNodes.has(nodeId)) {
        state.expandedNodes.delete(nodeId);
    } else {
        state.expandedNodes.add(nodeId);
    }
    renderTree();
}

// =============================================================================
// NODE SELECTION
// =============================================================================

function selectNode(nodeId, type, children = null) {
    state.selectedNode = nodeId;

    // Update active state in tree
    document.querySelectorAll('.tree-node-header').forEach(header => {
        header.classList.remove('active');
    });
    const nodeElement = document.querySelector(`[data-id="${nodeId}"] .tree-node-header`);
    if (nodeElement) {
        nodeElement.classList.add('active');
    }

    // Show details panel
    document.getElementById('emptyState').style.display = 'none';
    const detailsPanel = document.getElementById('detailsPanel');
    detailsPanel.style.display = 'block';

    // Update breadcrumb
    const breadcrumb = document.getElementById('breadcrumb');
    const parts = nodeId.split('.');
    breadcrumb.textContent = parts.slice(0, -1).join(' › ') || 'Root';

    // Update title
    document.getElementById('detailsTitle').textContent = nodeId;

    // Update type badge
    document.getElementById('scopeType').textContent = type.charAt(0).toUpperCase() + type.slice(1);

    // Load data for the node
    if (type === 'scope') {
        loadScopeData(nodeId);
        document.getElementById('namingSection').style.display = 'block';
        document.getElementById('addScopeContainer').style.display = 'none';
    } else if (type === 'domain') {
        loadDomainData(nodeId);
        document.getElementById('namingSection').style.display = 'none';
        document.getElementById('addScopeContainer').style.display = 'block';
    } else {
        document.getElementById('namingSection').style.display = 'none';
        document.getElementById('addScopeContainer').style.display = 'none';
    }
}

function loadScopeData(scopeId) {
    const workspace = state.taxonomy.workspaces.find(w => w.id === scopeId);

    if (!workspace) return;

    // Populate form fields
    document.getElementById('descriptionInput').value = workspace.description || '';
    document.getElementById('decisionsInput').value = workspace.decisions || '';
    document.getElementById('llmContextInput').value = workspace.llmContext || '';

    // Naming convention
    if (workspace.naming) {
        document.getElementById('prefixInput').value = workspace.naming.prefix || '';
        document.getElementById('formatInput').value = workspace.naming.format || '';
        document.getElementById('componentsInput').value = workspace.naming.components?.join(', ') || '';

        // Examples
        const examplesList = document.getElementById('examplesList');
        examplesList.innerHTML = '';
        if (workspace.naming.examples) {
            workspace.naming.examples.forEach((example, index) => {
                addExampleToList(example, index);
            });
        }
    }

    // Fetch actual items from database to show usage
    fetchScopeUsage(scopeId);
}

function loadDomainData(domainId) {
    // For domains, we show minimal info and allow adding scopes
    document.getElementById('descriptionInput').value = `Domain: ${domainId}`;
    document.getElementById('decisionsInput').value = '';
    document.getElementById('llmContextInput').value = '';
}

// =============================================================================
// UPDATING NODES
// =============================================================================

function updateSelectedNode() {
    if (!state.selectedNode) return;

    const workspace = state.taxonomy.workspaces.find(w => w.id === state.selectedNode);
    if (!workspace) return;

    // Update description
    workspace.description = document.getElementById('descriptionInput').value;
    workspace.decisions = document.getElementById('decisionsInput').value;
    workspace.llmContext = document.getElementById('llmContextInput').value;

    // Update naming convention
    if (!workspace.naming) {
        workspace.naming = {};
    }

    workspace.naming.prefix = document.getElementById('prefixInput').value;
    workspace.naming.format = document.getElementById('formatInput').value;

    const componentsText = document.getElementById('componentsInput').value;
    workspace.naming.components = componentsText
        .split(',')
        .map(c => c.trim())
        .filter(c => c.length > 0);

    // Update examples
    const exampleInputs = document.querySelectorAll('.example-item input');
    workspace.naming.examples = Array.from(exampleInputs)
        .map(input => input.value)
        .filter(v => v.trim().length > 0);

    markAsModified();
}

function markAsModified() {
    state.hasUnsavedChanges = true;
    document.getElementById('saveBtn').disabled = false;
    document.getElementById('discardBtn').disabled = false;
}

// =============================================================================
// EXAMPLES MANAGEMENT
// =============================================================================

function addExample() {
    const examplesList = document.getElementById('examplesList');
    const index = examplesList.children.length;
    addExampleToList('', index);
    markAsModified();
}

function addExampleToList(value, index) {
    const examplesList = document.getElementById('examplesList');

    const item = document.createElement('div');
    item.className = 'example-item';

    const input = document.createElement('input');
    input.type = 'text';
    input.value = value;
    input.placeholder = 'Enter example filename...';
    input.addEventListener('input', updateSelectedNode);

    const deleteBtn = document.createElement('button');
    deleteBtn.innerHTML = createSvg('x', '').outerHTML;
    deleteBtn.addEventListener('click', () => {
        item.remove();
        updateSelectedNode();
    });

    item.appendChild(input);
    item.appendChild(deleteBtn);
    examplesList.appendChild(item);
}

// =============================================================================
// MODAL OPERATIONS
// =============================================================================

function showAddModal(type) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    if (type === 'domain') {
        modalTitle.textContent = 'Add New Domain';
        modalBody.innerHTML = `
            <div class="form-group">
                <label for="newDomainName">Domain Name</label>
                <input type="text" id="newDomainName" class="form-control" placeholder="e.g., Personal, Finance, Work">
                <span class="form-helper">Choose a stable, long-lived area of life or work</span>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="createDomain()">Create Domain</button>
            </div>
        `;
    } else if (type === 'scope') {
        const domainParts = state.selectedNode.split('.');
        const domain = domainParts[1];

        modalTitle.textContent = `Add New Scope to ${domain}`;
        modalBody.innerHTML = `
            <div class="form-group">
                <label for="newScopeName">Scope Name</label>
                <input type="text" id="newScopeName" class="form-control" placeholder="e.g., Taxes, Health, Education">
                <span class="form-helper">1-2 words describing the classification</span>
            </div>
            <div class="form-group">
                <label for="newScopeDesc">Description</label>
                <textarea id="newScopeDesc" class="form-control" rows="3" placeholder="What belongs in this classification?"></textarea>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="createScope('${domain}')">Create Scope</button>
            </div>
        `;
    }

    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

function createDomain() {
    const name = document.getElementById('newDomainName').value.trim();

    if (!name) {
        showNotification('Please enter a domain name', 'error');
        return;
    }

    // Check if domain already exists
    const domainId = `KB.${name}`;
    const exists = state.taxonomy.workspaces.some(w => w.id.startsWith(domainId + '.'));

    if (exists) {
        showNotification('Domain already exists', 'error');
        return;
    }

    // Add a placeholder scope for the new domain
    const newWorkspace = {
        id: `${domainId}.Placeholder`,
        description: `Placeholder scope for ${name} domain. Add real scopes and delete this.`,
        naming: {
            prefix: 'PH',
            components: ['type', 'year'],
            format: '{prefix}-{type}-{year}',
            examples: []
        }
    };

    state.taxonomy.workspaces.push(newWorkspace);
    state.expandedNodes.add(domainId);

    markAsModified();
    renderTree();
    closeModal();
    showNotification(`Domain "${name}" created successfully`, 'success');
}

function createScope(domain) {
    const name = document.getElementById('newScopeName').value.trim();
    const description = document.getElementById('newScopeDesc').value.trim();

    if (!name) {
        showNotification('Please enter a scope name', 'error');
        return;
    }

    const scopeId = `KB.${domain}.${name}`;

    // Check if scope already exists
    const exists = state.taxonomy.workspaces.some(w => w.id === scopeId);

    if (exists) {
        showNotification('Scope already exists', 'error');
        return;
    }

    const newWorkspace = {
        id: scopeId,
        description: description || `Documents related to ${name}`,
        naming: {
            prefix: name.substring(0, 3).toUpperCase(),
            components: ['type', 'date'],
            format: '{prefix}-{type}-{date}',
            examples: []
        }
    };

    state.taxonomy.workspaces.push(newWorkspace);
    state.expandedNodes.add(`KB.${domain}`);

    markAsModified();
    renderTree();
    closeModal();
    selectNode(scopeId, 'scope');
    showNotification(`Scope "${name}" created successfully`, 'success');
}

function editNodeTitle() {
    const currentId = state.selectedNode;
    if (!currentId) return;

    const parts = currentId.split('.');
    const currentName = parts[parts.length - 1];

    const newName = prompt('Enter new name:', currentName);
    if (!newName || newName === currentName) return;

    const newId = [...parts.slice(0, -1), newName].join('.');

    // Update workspace
    const workspace = state.taxonomy.workspaces.find(w => w.id === currentId);
    if (workspace) {
        workspace.id = newId;
        state.selectedNode = newId;
        markAsModified();
        renderTree();
        selectNode(newId, 'scope');
        showNotification('Name updated successfully', 'success');
    }
}

function deleteNode() {
    if (!state.selectedNode) return;

    const nodeType = state.selectedNode.split('.').length === 2 ? 'domain' : 'scope';
    const itemType = nodeType === 'domain' ? 'domain and all its scopes' : 'scope';

    const confirmed = confirm(`Are you sure you want to delete this ${itemType}: "${state.selectedNode}"? This cannot be undone.`);
    if (!confirmed) return;

    if (nodeType === 'domain') {
        // Delete all scopes under this domain
        const domainPrefix = state.selectedNode + '.';
        const indicesToRemove = [];
        state.taxonomy.workspaces.forEach((workspace, index) => {
            if (workspace.id.startsWith(domainPrefix)) {
                indicesToRemove.push(index);
            }
        });

        // Remove in reverse order to maintain correct indices
        indicesToRemove.reverse().forEach(index => {
            state.taxonomy.workspaces.splice(index, 1);
        });

        showNotification(`Deleted domain "${state.selectedNode}" and ${indicesToRemove.length} scope(s)`, 'success');
    } else {
        // Delete single scope
        const index = state.taxonomy.workspaces.findIndex(w => w.id === state.selectedNode);
        if (index !== -1) {
            state.taxonomy.workspaces.splice(index, 1);
            showNotification('Scope deleted successfully', 'success');
        }
    }

    state.selectedNode = null;

    document.getElementById('emptyState').style.display = 'flex';
    document.getElementById('detailsPanel').style.display = 'none';

    markAsModified();
    renderTree();
}

// =============================================================================
// SEARCH
// =============================================================================

function handleSearch(event) {
    const query = event.target.value.toLowerCase();

    if (!query) {
        // Reset - show all nodes
        document.querySelectorAll('.tree-node').forEach(node => {
            node.style.display = 'block';
        });
        return;
    }

    // Filter nodes
    document.querySelectorAll('.tree-node').forEach(node => {
        const label = node.querySelector('.tree-node-label').textContent.toLowerCase();
        const id = node.dataset.id.toLowerCase();

        if (label.includes(query) || id.includes(query)) {
            node.style.display = 'block';
            // Expand parent
            let parent = node.parentElement.closest('.tree-node');
            while (parent) {
                const parentId = parent.dataset.id;
                state.expandedNodes.add(parentId);
                parent = parent.parentElement.closest('.tree-node');
            }
        } else {
            node.style.display = 'none';
        }
    });

    renderTree();
}

// =============================================================================
// SAVE / EXPORT
// =============================================================================

async function saveTaxonomy() {
    try {
        const yamlOutput = jsyaml.dump(state.taxonomy, {
            indent: 2,
            lineWidth: -1,
            noRefs: true
        });

        // In a real implementation, this would save to the server
        // For now, we'll just download it
        const blob = new Blob([yamlOutput], { type: 'text/yaml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'taxonomy.yaml';
        a.click();
        URL.revokeObjectURL(url);

        state.hasUnsavedChanges = false;
        document.getElementById('saveBtn').disabled = true;
        document.getElementById('discardBtn').disabled = true;

        showNotification('Taxonomy saved successfully!', 'success');
    } catch (error) {
        console.error('Error saving taxonomy:', error);
        showNotification('Error saving taxonomy', 'error');
    }
}

function discardChanges() {
    const confirmed = confirm('Discard all changes and reload the original taxonomy?');
    if (!confirmed) return;

    state.taxonomy = jsyaml.load(state.originalYaml);
    state.hasUnsavedChanges = false;
    document.getElementById('saveBtn').disabled = true;
    document.getElementById('discardBtn').disabled = true;

    renderTree();

    document.getElementById('emptyState').style.display = 'flex';
    document.getElementById('detailsPanel').style.display = 'none';

    showNotification('Changes discarded', 'success');
}

function exportYaml() {
    const yamlOutput = jsyaml.dump(state.taxonomy, {
        indent: 2,
        lineWidth: -1,
        noRefs: true
    });

    const blob = new Blob([yamlOutput], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `taxonomy-export-${Date.now()}.yaml`;
    a.click();
    URL.revokeObjectURL(url);

    showNotification('Taxonomy exported successfully!', 'success');
}

// =============================================================================
// VALIDATION
// =============================================================================

function validateTaxonomy() {
    const errors = [];
    const warnings = [];

    state.taxonomy.workspaces.forEach(workspace => {
        // Test 1: Clarity - must have a description
        if (!workspace.description || workspace.description.trim().length === 0) {
            errors.push(`${workspace.id}: Missing description`);
        }

        // Test 2: Decision linkage - should have decision support
        if (!workspace.decisions || workspace.decisions.trim().length === 0) {
            warnings.push(`${workspace.id}: No decision support specified`);
        }

        // Test 3: Naming convention
        if (!workspace.naming || !workspace.naming.prefix) {
            errors.push(`${workspace.id}: Missing naming convention`);
        }

        // Test 4: Examples
        if (!workspace.naming?.examples || workspace.naming.examples.length === 0) {
            warnings.push(`${workspace.id}: No examples provided`);
        }
    });

    // Show results
    let message = 'Validation Results:\n\n';

    if (errors.length === 0 && warnings.length === 0) {
        message = '✅ Taxonomy is valid! No errors or warnings found.';
        showNotification(message, 'success');
    } else {
        if (errors.length > 0) {
            message += `❌ ERRORS (${errors.length}):\n` + errors.join('\n') + '\n\n';
        }
        if (warnings.length > 0) {
            message += `⚠️  WARNINGS (${warnings.length}):\n` + warnings.join('\n');
        }
        alert(message);
    }
}

// =============================================================================
// UTILITIES
// =============================================================================

function createSvg(type, className = '') {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    if (className) svg.className = className;

    // Set explicit size for tree node icons
    if (className && className.includes('tree-node-icon')) {
        svg.setAttribute('width', '12');
        svg.setAttribute('height', '12');
    }

    // Set explicit size for expand/collapse icons
    if (className && className.includes('tree-expand-icon')) {
        svg.setAttribute('width', '12');
        svg.setAttribute('height', '12');
    }

    const paths = {
        'chevron-right': '<polyline points="9 18 15 12 9 6"></polyline>',
        'folder': '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>',
        'file': '<path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline>',
        'x': '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>'
    };

    if (paths[type]) {
        svg.innerHTML = paths[type];
    }

    return svg;
}

function showNotification(message, type = 'info') {
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#06b6d4'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        max-width: 400px;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// =============================================================================
// DATABASE INTEGRATION - Show actual files
// =============================================================================

async function fetchScopeUsage(scopeId) {
    try {
        // Query the backend API for items in this workspace
        const response = await fetch(`http://localhost:8765/api/items?workspace=${encodeURIComponent(scopeId)}&limit=1000`);
        if (!response.ok) {
            console.log('Could not fetch items from database');
            return;
        }

        const items = await response.json();
        console.log(`Found ${items.length} items for ${scopeId}`);

        // Group items by subpath
        const subpathGroups = {};
        items.forEach(item => {
            const subpath = item.proposed_subpath || '(root)';
            if (!subpathGroups[subpath]) {
                subpathGroups[subpath] = [];
            }
            subpathGroups[subpath].push(item);
        });

        // Display usage information
        displayScopeUsage(scopeId, items.length, subpathGroups);

    } catch (error) {
        console.log('Database not available or no items yet:', error);
        // Silently fail - database might not have data yet
    }
}

function displayScopeUsage(scopeId, totalItems, subpathGroups) {
    // Find or create usage section in the detail panel
    let usageSection = document.getElementById('scopeUsageSection');
    if (!usageSection) {
        // Create it after the naming section
        const namingSection = document.getElementById('namingSection');
        if (namingSection) {
            usageSection = document.createElement('div');
            usageSection.id = 'scopeUsageSection';
            usageSection.className = 'naming-section';
            namingSection.parentNode.insertBefore(usageSection, namingSection.nextSibling);
        } else {
            return; // Can't display if we don't have a place to put it
        }
    }

    // Build usage HTML
    let html = `
        <h4>📊 Actual Usage (from Database)</h4>
        <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 1rem;">
            <strong>${totalItems}</strong> file${totalItems !== 1 ? 's' : ''} classified into this scope
        </p>
    `;

    if (totalItems > 0) {
        html += '<div style="margin-top: 1rem;">';
        html += '<strong style="color: var(--text-primary); font-size: 0.875rem;">Subpaths:</strong>';
        html += '<ul style="list-style: none; padding: 0; margin-top: 0.5rem;">';

        // Sort subpaths
        const sortedSubpaths = Object.keys(subpathGroups).sort();
        sortedSubpaths.forEach(subpath => {
            const count = subpathGroups[subpath].length;
            const icon = subpath === '(root)' ? '📄' : '📁';
            html += `
                <li style="
                    padding: 0.5rem;
                    margin-bottom: 0.25rem;
                    background: var(--bg-primary);
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border: 1px solid var(--border-color);
                ">
                    <span style="color: var(--text-primary); font-size: 0.875rem;">
                        ${icon} ${subpath}
                    </span>
                    <span style="
                        color: var(--text-muted);
                        font-size: 0.75rem;
                        background: var(--bg-tertiary);
                        padding: 0.125rem 0.5rem;
                        border-radius: 12px;
                    ">
                        ${count} file${count !== 1 ? 's' : ''}
                    </span>
                </li>
            `;
        });

        html += '</ul></div>';
    } else {
        html += '<p style="color: var(--text-muted); font-size: 0.875rem; font-style: italic;">No files classified yet</p>';
    }

    usageSection.innerHTML = html;
}

