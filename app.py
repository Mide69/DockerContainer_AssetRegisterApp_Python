#!/usr/bin/env python3
"""
IT Asset Inventory Management System - Docker Version
Web-based interface for containerized deployment
"""

from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import csv
import io
import os
from datetime import datetime
import json
import threading
import time

# For barcode scanning via webcam (optional)
try:
    import cv2
    from pyzbar import pyzbar
    BARCODE_SUPPORT = True
except ImportError:
    BARCODE_SUPPORT = False

class AssetDatabase:
    def __init__(self, db_path="/app/data/asset_inventory.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with assets table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_number TEXT UNIQUE NOT NULL,
                serial_number TEXT,
                barcode TEXT UNIQUE,
                location TEXT,
                status TEXT,
                staff_name TEXT,
                staff_number TEXT,
                condition TEXT,
                date_added TEXT,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_asset(self, asset_data):
        """Add new asset to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO assets 
                (asset_number, serial_number, barcode, location, status, 
                 staff_name, staff_number, condition, date_added, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*asset_data, current_time, current_time))
            
            conn.commit()
            return {"success": True, "message": "Asset added successfully"}
        except sqlite3.IntegrityError as e:
            return {"success": False, "message": f"Error: {str(e)}"}
        finally:
            conn.close()
    
    def update_asset(self, asset_number, asset_data):
        """Update existing asset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                UPDATE assets SET
                serial_number = ?, barcode = ?, location = ?, status = ?,
                staff_name = ?, staff_number = ?, condition = ?, last_updated = ?
                WHERE asset_number = ?
            ''', (*asset_data[1:], current_time, asset_number))
            
            conn.commit()
            success = cursor.rowcount > 0
            return {"success": success, "message": "Asset updated successfully" if success else "Asset not found"}
        finally:
            conn.close()
    
    def get_asset(self, asset_number=None, barcode=None):
        """Retrieve asset by asset number or barcode"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if asset_number:
            cursor.execute('SELECT * FROM assets WHERE asset_number = ?', (asset_number,))
        elif barcode:
            cursor.execute('SELECT * FROM assets WHERE barcode = ?', (barcode,))
        else:
            return None
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "asset_number": result[1],
                "serial_number": result[2],
                "barcode": result[3],
                "location": result[4],
                "status": result[5],
                "staff_name": result[6],
                "staff_number": result[7],
                "condition": result[8],
                "date_added": result[9],
                "last_updated": result[10]
            }
        return None
    
    def get_all_assets(self):
        """Retrieve all assets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets ORDER BY asset_number')
        results = cursor.fetchall()
        conn.close()
        
        assets = []
        for result in results:
            assets.append({
                "id": result[0],
                "asset_number": result[1],
                "serial_number": result[2],
                "barcode": result[3],
                "location": result[4],
                "status": result[5],
                "staff_name": result[6],
                "staff_number": result[7],
                "condition": result[8],
                "date_added": result[9],
                "last_updated": result[10]
            })
        return assets
    
    def delete_asset(self, asset_number):
        """Delete asset from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM assets WHERE asset_number = ?', (asset_number,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return {"success": success, "message": "Asset deleted successfully" if success else "Asset not found"}

class BarcodeScanner:
    def __init__(self):
        self.scanning = False
        self.camera = None
        self.last_scan = None
    
    def scan_once(self):
        """Single barcode scan attempt"""
        if not BARCODE_SUPPORT:
            return {"success": False, "message": "Barcode scanning not available"}
        
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            return {"success": False, "message": "Could not access camera"}
        
        # Try to scan for 5 seconds
        start_time = time.time()
        while time.time() - start_time < 5:
            ret, frame = camera.read()
            if not ret:
                continue
            
            barcodes = pyzbar.decode(frame)
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8')
                camera.release()
                return {"success": True, "barcode": barcode_data}
            
            time.sleep(0.1)
        
        camera.release()
        return {"success": False, "message": "No barcode detected"}

# Flask Application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Initialize database
db = AssetDatabase()
scanner = BarcodeScanner()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', barcode_support=BARCODE_SUPPORT)

@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Get all assets"""
    assets = db.get_all_assets()
    return jsonify(assets)

@app.route('/api/assets', methods=['POST'])
def add_asset():
    """Add new asset"""
    data = request.json
    asset_data = (
        data.get('asset_number', ''),
        data.get('serial_number', ''),
        data.get('barcode', ''),
        data.get('location', ''),
        data.get('status', ''),
        data.get('staff_name', ''),
        data.get('staff_number', ''),
        data.get('condition', '')
    )
    
    result = db.add_asset(asset_data)
    return jsonify(result)

@app.route('/api/assets/<asset_number>', methods=['GET'])
def get_asset(asset_number):
    """Get specific asset"""
    asset = db.get_asset(asset_number=asset_number)
    if asset:
        return jsonify(asset)
    return jsonify({"success": False, "message": "Asset not found"}), 404

@app.route('/api/assets/<asset_number>', methods=['PUT'])
def update_asset(asset_number):
    """Update existing asset"""
    data = request.json
    asset_data = (
        data.get('asset_number', ''),
        data.get('serial_number', ''),
        data.get('barcode', ''),
        data.get('location', ''),
        data.get('status', ''),
        data.get('staff_name', ''),
        data.get('staff_number', ''),
        data.get('condition', '')
    )
    
    result = db.update_asset(asset_number, asset_data)
    return jsonify(result)

@app.route('/api/assets/<asset_number>', methods=['DELETE'])
def delete_asset(asset_number):
    """Delete asset"""
    result = db.delete_asset(asset_number)
    return jsonify(result)

@app.route('/api/assets/search/barcode/<barcode>', methods=['GET'])
def get_asset_by_barcode(barcode):
    """Get asset by barcode"""
    asset = db.get_asset(barcode=barcode)
    if asset:
        return jsonify(asset)
    return jsonify({"success": False, "message": "Asset not found"}), 404

@app.route('/api/scan', methods=['POST'])
def scan_barcode():
    """Scan barcode using camera"""
    result = scanner.scan_once()
    return jsonify(result)

@app.route('/api/export', methods=['GET'])
def export_csv():
    """Export assets to CSV"""
    assets = db.get_all_assets()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Asset Number', 'Serial Number', 'Barcode', 'Location', 
                    'Status', 'Staff Name', 'Staff Number', 'Condition', 
                    'Date Added', 'Last Updated'])
    
    # Write data
    for asset in assets:
        writer.writerow([
            asset['asset_number'], asset['serial_number'], asset['barcode'],
            asset['location'], asset['status'], asset['staff_name'],
            asset['staff_number'], asset['condition'], asset['date_added'],
            asset['last_updated']
        ])
    
    output.seek(0)
    
    # Create response
    response = app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=asset_inventory.csv'}
    )
    return response

@app.route('/health')
def health_check():
    """Health check endpoint for Docker"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# HTML Template (embedded for single-file deployment)
@app.before_first_request
def create_templates():
    """Create templates directory and files"""
    template_dir = "templates"
    os.makedirs(template_dir, exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Asset Inventory</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .scanner-section { background-color: #f8f9fa; border-radius: 10px; }
        .asset-form { background-color: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .table-container { max-height: 500px; overflow-y: auto; }
        .status-available { color: #28a745; }
        .status-assigned { color: #007bff; }
        .status-repair { color: #ffc107; }
        .status-retired { color: #6c757d; }
    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <div class="row">
            <div class="col-12">
                <h1 class="text-center mb-4"><i class="fas fa-laptop"></i> IT Asset Inventory System</h1>
            </div>
        </div>

        <!-- Barcode Scanner Section -->
        {% if barcode_support %}
        <div class="row mb-4">
            <div class="col-12">
                <div class="scanner-section p-3">
                    <h4><i class="fas fa-qrcode"></i> Barcode Scanner</h4>
                    <button id="scanBtn" class="btn btn-primary me-2">
                        <i class="fas fa-camera"></i> Scan Barcode
                    </button>
                    <span id="scanStatus" class="text-muted">Ready to scan</span>
                </div>
            </div>
        </div>
        {% endif %}

        <div class="row">
            <!-- Asset Entry Form -->
            <div class="col-lg-4">
                <div class="asset-form p-4 mb-4">
                    <h4><i class="fas fa-plus-circle"></i> Asset Entry</h4>
                    <form id="assetForm">
                        <div class="mb-3">
                            <label class="form-label">Asset Number *</label>
                            <input type="text" class="form-control" id="asset_number" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Serial Number</label>
                            <input type="text" class="form-control" id="serial_number">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Barcode</label>
                            <input type="text" class="form-control" id="barcode">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Location</label>
                            <input type="text" class="form-control" id="location">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Status</label>
                            <select class="form-select" id="status">
                                <option value="Available">Available</option>
                                <option value="Assigned">Assigned</option>
                                <option value="In Repair">In Repair</option>
                                <option value="Retired">Retired</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Staff Name</label>
                            <input type="text" class="form-control" id="staff_name">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Staff Number</label>
                            <input type="text" class="form-control" id="staff_number">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Condition</label>
                            <select class="form-select" id="condition">
                                <option value="Excellent">Excellent</option>
                                <option value="Good">Good</option>
                                <option value="Fair">Fair</option>
                                <option value="Poor">Poor</option>
                                <option value="Damaged">Damaged</option>
                            </select>
                        </div>
                        <div class="d-grid gap-2">
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-save"></i> Add Asset
                            </button>
                            <button type="button" class="btn btn-warning" id="updateBtn" style="display:none;">
                                <i class="fas fa-edit"></i> Update Asset
                            </button>
                            <button type="button" class="btn btn-secondary" id="clearBtn">
                                <i class="fas fa-eraser"></i> Clear Form
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Asset List -->
            <div class="col-lg-8">
                <div class="asset-form p-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h4><i class="fas fa-list"></i> Asset Inventory</h4>
                        <div>
                            <button class="btn btn-info btn-sm me-2" id="refreshBtn">
                                <i class="fas fa-sync"></i> Refresh
                            </button>
                            <button class="btn btn-success btn-sm" id="exportBtn">
                                <i class="fas fa-download"></i> Export CSV
                            </button>
                        </div>
                    </div>
                    <div class="table-container">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark sticky-top">
                                <tr>
                                    <th>Asset #</th>
                                    <th>Serial #</th>
                                    <th>Location</th>
                                    <th>Status</th>
                                    <th>Staff</th>
                                    <th>Condition</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="assetTableBody">
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Success/Error Messages -->
    <div id="alertContainer" class="position-fixed top-0 end-0 p-3" style="z-index: 9999;"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.1.3/js/bootstrap.bundle.min.js"></script>
    <script>
        let editingAsset = null;

        // Load assets on page load
        document.addEventListener('DOMContentLoaded', loadAssets);

        // Form submission
        document.getElementById('assetForm').addEventListener('submit', function(e) {
            e.preventDefault();
            if (editingAsset) {
                updateAsset();
            } else {
                addAsset();
            }
        });

        // Button event listeners
        document.getElementById('clearBtn').addEventListener('click', clearForm);
        document.getElementById('refreshBtn').addEventListener('click', loadAssets);
        document.getElementById('exportBtn').addEventListener('click', exportCSV);
        document.getElementById('updateBtn').addEventListener('click', updateAsset);

        {% if barcode_support %}
        document.getElementById('scanBtn').addEventListener('click', scanBarcode);
        {% endif %}

        function showAlert(message, type = 'success') {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.getElementById('alertContainer').appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 5000);
        }

        function getFormData() {
            return {
                asset_number: document.getElementById('asset_number').value,
                serial_number: document.getElementById('serial_number').value,
                barcode: document.getElementById('barcode').value,
                location: document.getElementById('location').value,
                status: document.getElementById('status').value,
                staff_name: document.getElementById('staff_name').value,
                staff_number: document.getElementById('staff_number').value,
                condition: document.getElementById('condition').value
            };
        }

        function populateForm(asset) {
            document.getElementById('asset_number').value = asset.asset_number || '';
            document.getElementById('serial_number').value = asset.serial_number || '';
            document.getElementById('barcode').value = asset.barcode || '';
            document.getElementById('location').value = asset.location || '';
            document.getElementById('status').value = asset.status || '';
            document.getElementById('staff_name').value = asset.staff_name || '';
            document.getElementById('staff_number').value = asset.staff_number || '';
            document.getElementById('condition').value = asset.condition || '';
        }

        function clearForm() {
            document.getElementById('assetForm').reset();
            editingAsset = null;
            document.querySelector('button[type="submit"]').style.display = 'block';
            document.getElementById('updateBtn').style.display = 'none';
        }

        async function addAsset() {
            try {
                const response = await fetch('/api/assets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(getFormData())
                });
                const result = await response.json();
                
                if (result.success) {
                    showAlert('Asset added successfully!');
                    clearForm();
                    loadAssets();
                } else {
                    showAlert(result.message, 'danger');
                }
            } catch (error) {
                showAlert('Error adding asset', 'danger');
            }
        }

        async function updateAsset() {
            if (!editingAsset) return;
            
            try {
                const response = await fetch(`/api/assets/${editingAsset}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(getFormData())
                });
                const result = await response.json();
                
                if (result.success) {
                    showAlert('Asset updated successfully!');
                    clearForm();
                    loadAssets();
                } else {
                    showAlert(result.message, 'danger');
                }
            } catch (error) {
                showAlert('Error updating asset', 'danger');
            }
        }

        async function loadAssets() {
            try {
                const response = await fetch('/api/assets');
                const assets = await response.json();
                
                const tbody = document.getElementById('assetTableBody');
                tbody.innerHTML = '';
                
                assets.forEach(asset => {
                    const row = tbody.insertRow();
                    row.innerHTML = `
                        <td>${asset.asset_number}</td>
                        <td>${asset.serial_number || '-'}</td>
                        <td>${asset.location || '-'}</td>
                        <td><span class="status-${asset.status.toLowerCase().replace(' ', '-')}">${asset.status}</span></td>
                        <td>${asset.staff_name || '-'}</td>
                        <td>${asset.condition || '-'}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary me-1" onclick="editAsset('${asset.asset_number}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteAsset('${asset.asset_number}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    `;
                });
            } catch (error) {
                showAlert('Error loading assets', 'danger');
            }
        }

        async function editAsset(assetNumber) {
            try {
                const response = await fetch(`/api/assets/${assetNumber}`);
                const asset = await response.json();
                
                if (asset.asset_number) {
                    populateForm(asset);
                    editingAsset = assetNumber;
                    document.querySelector('button[type="submit"]').style.display = 'none';
                    document.getElementById('updateBtn').style.display = 'block';
                }
            } catch (error) {
                showAlert('Error loading asset for editing', 'danger');
            }
        }

        async function deleteAsset(assetNumber) {
            if (!confirm(`Are you sure you want to delete asset ${assetNumber}?`)) return;
            
            try {
                const response = await fetch(`/api/assets/${assetNumber}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                
                if (result.success) {
                    showAlert('Asset deleted successfully!');
                    loadAssets();
                } else {
                    showAlert(result.message, 'danger');
                }
            } catch (error) {
                showAlert('Error deleting asset', 'danger');
            }
        }

        {% if barcode_support %}
        async function scanBarcode() {
            const scanBtn = document.getElementById('scanBtn');
            const scanStatus = document.getElementById('scanStatus');
            
            scanBtn.disabled = true;
            scanStatus.textContent = 'Scanning... Point camera at barcode';
            
            try {
                const response = await fetch('/api/scan', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('barcode').value = result.barcode;
                    scanStatus.textContent = `Scanned: ${result.barcode}`;
                    
                    // Try to load existing asset
                    const assetResponse = await fetch(`/api/assets/search/barcode/${result.barcode}`);
                    if (assetResponse.ok) {
                        const asset = await assetResponse.json();
                        populateForm(asset);
                        editingAsset = asset.asset_number;
                        document.querySelector('button[type="submit"]').style.display = 'none';
                        document.getElementById('updateBtn').style.display = 'block';
                        showAlert('Existing asset loaded for editing', 'info');
                    }
                } else {
                    scanStatus.textContent = result.message;
                    showAlert(result.message, 'warning');
                }
            } catch (error) {
                scanStatus.textContent = 'Scan failed';
                showAlert('Scanning failed', 'danger');
            } finally {
                scanBtn.disabled = false;
                setTimeout(() => {
                    scanStatus.textContent = 'Ready to scan';
                }, 3000);
            }
        }
        {% endif %}

        function exportCSV() {
            window.location.href = '/api/export';
        }
    </script>
</body>
</html>'''
    
    with open(os.path.join(template_dir, 'index.html'), 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting IT Asset Inventory System on {host}:{port}")
    print(f"Barcode scanning support: {'Available' if BARCODE_SUPPORT else 'Not available'}")
    
    app.run(host=host, port=port, debug=debug)