// TonerTrack Frontend Application
let printers = {};
let selectedPrinterIP = null;
let searchQuery = '';
let filterStatus = 'All';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadPrinters();
    setupEventListeners();
    
    // Set initial mobile view
    const mainContent = document.querySelector('.main-content');
    if (window.innerWidth <= 768) {
        console.log('Mobile view detected, setting show-list class');
        mainContent.classList.add('show-list');
    }
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            // Desktop view - remove mobile classes
            mainContent.classList.remove('show-list', 'show-details');
        } else if (window.innerWidth <= 768 && !mainContent.classList.contains('show-list') && !mainContent.classList.contains('show-details')) {
            // Mobile view without class - default to list
            mainContent.classList.add('show-list');
        }
    });
    
    // Auto-refresh every 5 minutes
    setInterval(() => {
        if (!document.getElementById('refreshSpinner').classList.contains('active')) {
            loadPrinters();
        }
    }, 5 * 60 * 1000);
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('refreshAllBtn').addEventListener('click', refreshAllPrinters);
    document.getElementById('addPrinterBtn').addEventListener('click', openAddPrinterModal);
    document.getElementById('exportBtn').addEventListener('click', exportPrinters);
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    document.getElementById('filterSelect').addEventListener('change', handleFilter);
}

// Load all printers
async function loadPrinters() {
    try {
        const response = await fetch('/api/printers');
        const data = await response.json();
        printers = data.printers;
        
        renderPrinterList();
        updateStats();
        
        // Re-render details if a printer is selected
        if (selectedPrinterIP && printers[selectedPrinterIP]) {
            showPrinterDetails(selectedPrinterIP);
        }
    } catch (error) {
        console.error('Error loading printers:', error);
        showNotification('Failed to load printers', 'error');
    }
}

// Render printer list
function renderPrinterList() {
    const listContainer = document.getElementById('printerList');
    listContainer.innerHTML = '';
    
    // Filter printers
    const filteredPrinters = Object.entries(printers).filter(([ip, printer]) => {
        const matchesSearch = printer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            ip.includes(searchQuery);
        const matchesFilter = filterStatus === 'All' || printer.status === filterStatus;
        return matchesSearch && matchesFilter;
    });
    
    if (filteredPrinters.length === 0) {
        listContainer.innerHTML = '<div class="empty-state-small"><p>No printers found</p></div>';
        return;
    }
    
    // Sort by name
    filteredPrinters.sort((a, b) => a[1].name.localeCompare(b[1].name));
    
    filteredPrinters.forEach(([ip, printer]) => {
        const item = document.createElement('div');
        item.className = `printer-item status-${printer.status.toLowerCase()}`;
        if (ip === selectedPrinterIP) {
            item.classList.add('selected');
        }
        
        item.innerHTML = `
            <div class="status-dot ${printer.status.toLowerCase()}"></div>
            <div class="printer-info">
                <div class="printer-name">${escapeHtml(printer.name)}</div>
                <div class="printer-ip">${escapeHtml(ip)}</div>
            </div>
        `;
        
        item.addEventListener('click', () => selectPrinter(ip));
        listContainer.appendChild(item);
    });
}

// Select a printer
function selectPrinter(ip) {
    console.log('=== selectPrinter called ===');
    console.log('IP:', ip);
    console.log('Window width:', window.innerWidth);
    console.log('Current printers data:', printers);
    
    selectedPrinterIP = ip;
    renderPrinterList(); // Re-render to update selection
    
    console.log('Calling showPrinterDetails...');
    showPrinterDetails(ip);
    
    // Update alerts panel to show only this printer's alerts
    updateAlertsPanel();
    
    // On mobile, switch to details view
    if (window.innerWidth <= 768) {
        console.log('Mobile: Switching to details view for', ip);
        const mainContent = document.querySelector('.main-content');
        console.log('Main content element:', mainContent);
        console.log('Classes before:', mainContent.className);
        
        mainContent.classList.remove('show-list');
        mainContent.classList.add('show-details');
        
        console.log('Classes after:', mainContent.className);
        
        // Force check visibility
        const centerPanel = document.querySelector('.center-panel');
        console.log('Center panel display:', window.getComputedStyle(centerPanel).display);
        console.log('Center panel visibility:', window.getComputedStyle(centerPanel).visibility);
    }
}

// Show printer list (mobile back button)
function showPrinterList() {
    console.log('Mobile: Returning to printer list');
    const mainContent = document.querySelector('.main-content');
    mainContent.classList.remove('show-details');
    mainContent.classList.add('show-list');
    console.log('Classes now:', mainContent.className);
    
    // Clear selection and show all alerts
    clearPrinterSelection();
}

// Clear printer selection (show all alerts)
function clearPrinterSelection() {
    selectedPrinterIP = null;
    renderPrinterList();
    updateAlertsPanel();
    
    // Show empty state in details
    document.getElementById('printerDetails').innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">🖨️</div>
            <h2>Select a Printer</h2>
            <p>Choose a printer from the list to view details</p>
        </div>
    `;
}

// Show printer details
function showPrinterDetails(ip) {
    console.log('=== showPrinterDetails called ===');
    console.log('IP:', ip);
    
    const printer = printers[ip];
    console.log('Printer data:', printer);
    
    if (!printer) {
        console.error('Printer not found for IP:', ip);
        return;
    }
    
    const detailsContainer = document.getElementById('printerDetails');
    console.log('Details container:', detailsContainer);
    
    // Determine status badge color
    const statusClass = printer.status.toLowerCase();
    const statusColors = {
        'ok': '#3adb76',
        'warning': '#ffae42',
        'error': '#ff5c5c',
        'offline': '#9e9e9e'
    };
    
    detailsContainer.innerHTML = `
        <div class="details-header">
            <div class="details-title">
                <h2>${escapeHtml(printer.name)}</h2>
                <div class="ip">${escapeHtml(ip)}</div>
            </div>
            <div class="details">
                <button class="btn btn-primary" onclick="pollPrinter('${ip}')">🔄 Refresh</button>
                <button class="btn btn-secondary" onclick="openEditPrinterModal('${ip}')">✏️ Edit</button>
                <button class="btn btn-danger" onclick="deletePrinter('${ip}')">🗑️ Delete</button>
            </div>
        </div>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value" style="color: ${statusColors[statusClass]}">${printer.status}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Model</div>
                <div class="info-value">${escapeHtml(printer.model)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Serial Number</div>
                <div class="info-value">${escapeHtml(printer.serial)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Last Updated</div>
                <div class="info-value">${escapeHtml(printer.timestamp)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Total Pages</div>
                <div class="info-value">${escapeHtml(printer.total_pages)}</div>
            </div>
        </div>
        
        ${renderSuppliesSection('🖋️ Toner Cartridges', printer.toner_cartridges)}
        ${renderSuppliesSection('🥁 Drum Units', printer.drum_units)}
        ${renderSuppliesSection('🔧 Other Supplies', printer.other)}
    `;
    
    // Update alerts panel
    updateAlertsPanel();
}

// Render supplies section
function renderSuppliesSection(title, supplies) {
    if (!supplies || Object.keys(supplies).length === 0) {
        return '';
    }
    
    let html = `<div class="supplies-section"><h3>${title}</h3>`;
    
    Object.entries(supplies).forEach(([name, level]) => {
        let levelClass = 'high';
        if (level.endsWith('%')) {
            const percent = parseInt(level);
            if (percent < 10) levelClass = 'low';
            else if (percent < 20) levelClass = 'medium';
        } else if (level === 'Unknown' || level === 'N/A') {
            levelClass = 'medium';
        }
        
        html += `
            <div class="supply-item">
                <div class="supply-name">${escapeHtml(name)}</div>
                <div class="supply-level ${levelClass}">${escapeHtml(level)}</div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// Update alerts panel
function updateAlertsPanel() {
    const alertsContainer = document.getElementById('alertsList');
    const panelHeader = document.querySelector('.right-panel .panel-header');
    const alerts = [];
    
    // If a printer is selected, show only its alerts
    if (selectedPrinterIP && printers[selectedPrinterIP]) {
        const printer = printers[selectedPrinterIP];
        
        panelHeader.innerHTML = `
            <h3 style="cursor: pointer; display: flex; align-items: center; gap: 8px;" 
                onclick="clearPrinterSelection()" 
                title="Click to show all alerts">
                <span>Alerts: ${escapeHtml(printer.name)}</span>
                <span style="font-size: 0.8em; opacity: 0.7;">✕</span>
            </h3>
        `;
        
        if (printer.errors && Object.keys(printer.errors).length > 0) {
            Object.entries(printer.errors).forEach(([message, severity]) => {
                alerts.push({
                    printer: printer.name,
                    ip: selectedPrinterIP,
                    message: message,
                    severity: severity
                });
            });
        }
    } else {
        // No printer selected - show all alerts
        panelHeader.innerHTML = '<h3>All Alerts</h3>';
        
        Object.entries(printers).forEach(([ip, printer]) => {
            if (printer.errors && Object.keys(printer.errors).length > 0) {
                Object.entries(printer.errors).forEach(([message, severity]) => {
                    alerts.push({
                        printer: printer.name,
                        ip: ip,
                        message: message,
                        severity: severity
                    });
                });
            }
        });
    }
    
    if (alerts.length === 0) {
        const noAlertsMsg = selectedPrinterIP ? 'No alerts for this printer' : 'No active alerts';
        alertsContainer.innerHTML = `<div class="empty-state-small"><p>${noAlertsMsg}</p></div>`;
        return;
    }
    
    alertsContainer.innerHTML = '';
    alerts.forEach(alert => {
        const alertClass = categorizeAlert(alert.message);
        const item = document.createElement('div');
        item.className = `alert-item ${alertClass}`;
        
        // Only show printer name if displaying all alerts (not filtered)
        const printerLabel = selectedPrinterIP ? '' : `<div class="alert-printer">${escapeHtml(alert.printer)}</div>`;
        
        item.innerHTML = `
            ${printerLabel}
            <div class="alert-message">${escapeHtml(alert.message)}</div>
        `;
        
        // Only make clickable if showing all alerts (to switch to that printer)
        if (!selectedPrinterIP) {
            item.style.cursor = 'pointer';
            item.addEventListener('click', () => selectPrinter(alert.ip));
        }
        
        alertsContainer.appendChild(item);
    });
}

// Categorize alert type for styling
function categorizeAlert(message) {
    const msg = message.toLowerCase();
    if (msg.includes('paper') && (msg.includes('out') || msg.includes('empty'))) {
        return 'paper';
    } else if (msg.includes('toner') && (msg.includes('low') || msg.includes('replace'))) {
        return 'warning';
    }
    return 'critical';
}

// Update statistics
function updateStats() {
    const stats = {
        total: 0,
        ok: 0,
        warning: 0,
        error: 0,
        offline: 0
    };
    
    Object.values(printers).forEach(printer => {
        stats.total++;
        const status = printer.status.toLowerCase();
        if (stats[status] !== undefined) {
            stats[status]++;
        }
    });
    
    document.getElementById('statTotal').textContent = stats.total;
    document.getElementById('statOk').textContent = stats.ok;
    document.getElementById('statWarning').textContent = stats.warning;
    document.getElementById('statError').textContent = stats.error;
    document.getElementById('statOffline').textContent = stats.offline;
}

// Refresh all printers
async function refreshAllPrinters() {
    const btn = document.getElementById('refreshAllBtn');
    const spinner = document.getElementById('refreshSpinner');
    
    btn.disabled = true;
    spinner.classList.add('active');
    
    try {
        const printerCount = Object.keys(printers).length;
        showNotification(`Starting to poll ${printerCount} printers...`, 'info');
        
        await fetch('/api/printers/poll-all', { method: 'POST' });
        
        let lastUpdateTime = Date.now();
        
        // Poll for completion every 2 seconds and auto-update
        const checkInterval = setInterval(async () => {
            const statusResponse = await fetch('/api/polling-status');
            const statusData = await statusResponse.json();
            
            // Auto-refresh data every 5 seconds during polling to show progress
            if (Date.now() - lastUpdateTime > 5000) {
                await loadPrinters();
                lastUpdateTime = Date.now();
            }
            
            if (!statusData.is_polling) {
                clearInterval(checkInterval);
                
                // Final auto-reload when done
                await loadPrinters();
                
                btn.disabled = false;
                spinner.classList.remove('active');
                showNotification(`All ${printerCount} printers refreshed successfully!`, 'success');
            }
        }, 2000);
        
    } catch (error) {
        console.error('Error refreshing printers:', error);
        showNotification('Failed to refresh printers', 'error');
        btn.disabled = false;
        spinner.classList.remove('active');
    }
}

// Poll single printer
async function pollPrinter(ip) {
    try {
        showNotification(`Polling ${printers[ip].name}...`, 'info');
        const response = await fetch(`/api/printers/${ip}/poll`, { method: 'POST' });
        
        if (response.ok) {
            // Auto-reload all printers to update the list and details
            await loadPrinters();
            
            // If this printer is currently selected, refresh its details
            if (selectedPrinterIP === ip) {
                showPrinterDetails(ip);
            }
            
            showNotification('Printer updated successfully!', 'success');
        } else {
            throw new Error('Poll failed');
        }
    } catch (error) {
        console.error('Error polling printer:', error);
        showNotification('Failed to poll printer', 'error');
    }
}

// Add printer modal
function openAddPrinterModal() {
    document.getElementById('addPrinterModal').classList.add('active');
    document.getElementById('printerName').value = '';
    document.getElementById('printerIP').value = '';
    document.getElementById('printerCommunity').value = 'public';
}

function closeAddPrinterModal() {
    document.getElementById('addPrinterModal').classList.remove('active');
}

async function savePrinter() {
    const name = document.getElementById('printerName').value.trim();
    const ip = document.getElementById('printerIP').value.trim();
    const community = document.getElementById('printerCommunity').value.trim() || 'public';
    
    if (!name || !ip) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/printers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, ip, community })
        });
        
        if (response.ok) {
            closeAddPrinterModal();
            await loadPrinters();
            showNotification('Printer added successfully', 'success');
            
            // Auto-poll the new printer
            setTimeout(() => pollPrinter(ip), 500);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to add printer', 'error');
        }
    } catch (error) {
        console.error('Error adding printer:', error);
        showNotification('Failed to add printer', 'error');
    }
}

// Edit printer modal
function openEditPrinterModal(ip) {
    const printer = printers[ip];
    document.getElementById('editPrinterModal').classList.add('active');
    document.getElementById('editPrinterName').value = printer.name;
    document.getElementById('editPrinterCommunity').value = printer.community || 'public';
    document.getElementById('editPrinterIP').value = ip;
}

function closeEditPrinterModal() {
    document.getElementById('editPrinterModal').classList.remove('active');
}

async function updatePrinter() {
    const ip = document.getElementById('editPrinterIP').value;
    const name = document.getElementById('editPrinterName').value.trim();
    const community = document.getElementById('editPrinterCommunity').value.trim();
    
    if (!name) {
        showNotification('Printer name is required', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/printers/${ip}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, community })
        });
        
        if (response.ok) {
            closeEditPrinterModal();
            await loadPrinters();
            showNotification('Printer updated successfully', 'success');
        } else {
            throw new Error('Update failed');
        }
    } catch (error) {
        console.error('Error updating printer:', error);
        showNotification('Failed to update printer', 'error');
    }
}

// Delete printer
async function deletePrinter(ip) {
    if (!confirm(`Are you sure you want to delete ${printers[ip].name}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/printers/${ip}`, { method: 'DELETE' });
        
        if (response.ok) {
            selectedPrinterIP = null;
            await loadPrinters();
            document.getElementById('printerDetails').innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🖨️</div>
                    <h2>Select a Printer</h2>
                    <p>Choose a printer from the list to view details</p>
                </div>
            `;
            showNotification('Printer deleted', 'success');
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Error deleting printer:', error);
        showNotification('Failed to delete printer', 'error');
    }
}

// Export printers
async function exportPrinters() {
    try {
        const response = await fetch('/api/export');
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tonertrack_export_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        showNotification('Export successful', 'success');
    } catch (error) {
        console.error('Error exporting:', error);
        showNotification('Export failed', 'error');
    }
}

// Search handler
function handleSearch(event) {
    searchQuery = event.target.value;
    renderPrinterList();
}

// Filter handler
function handleFilter(event) {
    filterStatus = event.target.value;
    renderPrinterList();
}

// Show notification (toast)
function showNotification(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const colors = {
        success: '#3adb76',
        error: '#ff5c5c',
        warning: '#ffae42',
        info: '#00bfff'
    };
    
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.style.cssText = `
        background: #2a2a2a;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        border-left: 4px solid ${colors[type]};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        min-width: 250px;
        max-width: 400px;
        animation: slideIn 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    `;
    
    toast.innerHTML = `
        <span style="font-size: 1.2em; color: ${colors[type]}">${icons[type]}</span>
        <span style="flex: 1">${escapeHtml(message)}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
    
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Add CSS animations
if (!document.getElementById('toastStyles')) {
    const style = document.createElement('style');
    style.id = 'toastStyles';
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
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}