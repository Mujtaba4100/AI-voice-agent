# ============================================================================
# Windows Firewall Setup - AI Voice Agent
# ============================================================================
# This script configures Windows Firewall rules for the AI Voice Agent
#
# IMPORTANT: Must be run as Administrator
#
# Usage: Run PowerShell as Administrator, then:
#        .\setup_firewall.ps1
# ============================================================================

#Requires -RunAsAdministrator

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🔥 Windows Firewall Configuration - AI Voice Agent" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CONFIGURATION
# ============================================================================

$RuleName = "AI Voice Agent"
$Ports = @{
    HTTP = 80
    Backend1 = 8000
    Backend2 = 8001
    Backend3 = 8002
    Streamlit = 8501
}

# ============================================================================
# CHECK ADMIN PRIVILEGES
# ============================================================================

$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script must be run as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "To run as Administrator:" -ForegroundColor Yellow
    Write-Host "1. Right-click PowerShell" -ForegroundColor Gray
    Write-Host "2. Select 'Run as Administrator'" -ForegroundColor Gray
    Write-Host "3. Navigate to this directory" -ForegroundColor Gray
    Write-Host "4. Run: .\setup_firewall.ps1" -ForegroundColor Gray
    exit 1
}

Write-Host "✓ Running with Administrator privileges" -ForegroundColor Green
Write-Host ""

# ============================================================================
# REMOVE EXISTING RULES
# ============================================================================

Write-Host "🔄 Checking for existing firewall rules..." -ForegroundColor Yellow

$existingRules = Get-NetFirewallRule -DisplayName "$RuleName*" -ErrorAction SilentlyContinue

if ($existingRules) {
    Write-Host "   Found $($existingRules.Count) existing rule(s)" -ForegroundColor Gray
    
    $answer = Read-Host "Remove existing rules? (Y/n)"
    if ($answer -ne "n" -and $answer -ne "N") {
        $existingRules | Remove-NetFirewallRule
        Write-Host "   ✓ Removed existing rules" -ForegroundColor Green
    }
}
else {
    Write-Host "   No existing rules found" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# CREATE FIREWALL RULES
# ============================================================================

Write-Host "🔄 Creating firewall rules..." -ForegroundColor Yellow
Write-Host ""

$rulesCreated = 0
$rulesFailed = 0

# Main HTTP rule (port 80) - Most important
try {
    Write-Host "Creating rule: $RuleName - HTTP (Port 80)" -ForegroundColor Cyan
    New-NetFirewallRule `
        -DisplayName "$RuleName - HTTP" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $Ports.HTTP `
        -Action Allow `
        -Profile Domain,Private,Public `
        -Description "Allow HTTP access to AI Voice Agent web interface" `
        -ErrorAction Stop | Out-Null
    
    Write-Host "   ✓ HTTP rule created (Port 80)" -ForegroundColor Green
    $rulesCreated++
}
catch {
    Write-Host "   ❌ Failed to create HTTP rule: $_" -ForegroundColor Red
    $rulesFailed++
}

# Backend API rules (optional - if accessing directly)
$createBackendRules = Read-Host "`nCreate rules for backend ports (8000-8002)? (y/N)"

if ($createBackendRules -eq "y" -or $createBackendRules -eq "Y") {
    try {
        Write-Host "Creating rule: Backend API Ports" -ForegroundColor Cyan
        New-NetFirewallRule `
            -DisplayName "$RuleName - Backend API" `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort @($Ports.Backend1, $Ports.Backend2, $Ports.Backend3) `
            -Action Allow `
            -Profile Domain,Private `
            -Description "Allow direct access to AI Voice Agent backend API workers" `
            -ErrorAction Stop | Out-Null
        
        Write-Host "   ✓ Backend API rules created (Ports 8000-8002)" -ForegroundColor Green
        $rulesCreated++
    }
    catch {
        Write-Host "   ❌ Failed to create backend rules: $_" -ForegroundColor Red
        $rulesFailed++
    }
}

# Streamlit rule (optional - if accessing directly)
$createStreamlitRule = Read-Host "`nCreate rule for Streamlit port (8501)? (y/N)"

if ($createStreamlitRule -eq "y" -or $createStreamlitRule -eq "Y") {
    try {
        Write-Host "Creating rule: Streamlit UI" -ForegroundColor Cyan
        New-NetFirewallRule `
            -DisplayName "$RuleName - Streamlit" `
            -Direction Inbound `
            -Protocol TCP `
            -LocalPort $Ports.Streamlit `
            -Action Allow `
            -Profile Domain,Private `
            -Description "Allow direct access to AI Voice Agent Streamlit UI" `
            -ErrorAction Stop | Out-Null
        
        Write-Host "   ✓ Streamlit rule created (Port 8501)" -ForegroundColor Green
        $rulesCreated++
    }
    catch {
        Write-Host "   ❌ Failed to create Streamlit rule: $_" -ForegroundColor Red
        $rulesFailed++
    }
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "📊 Firewall Configuration Summary" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Rules Created: $rulesCreated" -ForegroundColor Green
Write-Host "Rules Failed: $rulesFailed" -ForegroundColor $(if ($rulesFailed -gt 0) { "Red" } else { "Gray" })
Write-Host ""

# Display created rules
Write-Host "🔍 Active Firewall Rules:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "$RuleName*" | ForEach-Object {
    $portFilter = $_ | Get-NetFirewallPortFilter
    $status = if ($_.Enabled) { "✓ Enabled" } else { "✗ Disabled" }
    
    Write-Host "   $status - $($_.DisplayName)" -ForegroundColor $(if ($_.Enabled) { "Green" } else { "Yellow" })
    Write-Host "      Direction: $($_.Direction)" -ForegroundColor Gray
    Write-Host "      Action: $($_.Action)" -ForegroundColor Gray
    Write-Host "      Ports: $($portFilter.LocalPort)" -ForegroundColor Gray
    Write-Host "      Profile: $($_.Profile)" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# VERIFICATION
# ============================================================================

Write-Host "🔍 Verification:" -ForegroundColor Cyan

# Test if port 80 is allowed
$httpRule = Get-NetFirewallRule -DisplayName "$RuleName - HTTP" -ErrorAction SilentlyContinue

if ($httpRule -and $httpRule.Enabled) {
    Write-Host "   ✓ Port 80 (HTTP) is allowed" -ForegroundColor Green
}
else {
    Write-Host "   ❌ Port 80 (HTTP) is NOT allowed" -ForegroundColor Red
}

Write-Host ""

# ============================================================================
# ADDITIONAL RECOMMENDATIONS
# ============================================================================

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "📝 Additional Recommendations" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Public Network Access:" -ForegroundColor Yellow
Write-Host "   If accessing from public networks, ensure rules include 'Public' profile" -ForegroundColor Gray
Write-Host "   Current rules use: Domain, Private, Public" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Security Considerations:" -ForegroundColor Yellow
Write-Host "   • Only expose port 80 externally (via router)" -ForegroundColor Gray
Write-Host "   • Keep backend ports (8000-8002) internal only" -ForegroundColor Gray
Write-Host "   • Consider adding authentication for production use" -ForegroundColor Gray
Write-Host ""

Write-Host "3. Testing:" -ForegroundColor Yellow
Write-Host "   Test access from another device on your network:" -ForegroundColor Gray
Write-Host "   http://YOUR_LOCAL_IP" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. View All Firewall Rules:" -ForegroundColor Yellow
Write-Host "   Run: Get-NetFirewallRule | Where-Object DisplayName -like '*AI Voice*'" -ForegroundColor Gray
Write-Host ""

Write-Host "5. Disable Rules (if needed):" -ForegroundColor Yellow
Write-Host "   Run: Disable-NetFirewallRule -DisplayName 'AI Voice Agent*'" -ForegroundColor Gray
Write-Host ""

Write-Host "6. Remove Rules (if needed):" -ForegroundColor Yellow
Write-Host "   Run: Remove-NetFirewallRule -DisplayName 'AI Voice Agent*'" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# OPEN FIREWALL GUI
# ============================================================================

$openGUI = Read-Host "Open Windows Firewall GUI to verify? (y/N)"

if ($openGUI -eq "y" -or $openGUI -eq "Y") {
    Start-Process "wf.msc"
}

Write-Host ""
Write-Host "✅ Firewall configuration complete!" -ForegroundColor Green
Write-Host ""
