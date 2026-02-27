# Port Forwarding Guide - AI Voice Agent

## 📋 Overview

This guide explains how to configure your router to allow external access to your AI Voice Agent, enabling you to use it from outside your home network.

⚠️ **Security Warning**: Exposing services to the internet carries risks. Follow all security recommendations.

---

## 🎯 Prerequisites

Before setting up port forwarding:

- ✅ AI Voice Agent working locally (http://localhost)
- ✅ Windows Firewall configured (port 80 allowed)
- ✅ Static local IP assigned to your computer
- ✅ Router admin access credentials
- ✅ Understanding of security implications

---

## 🔧 Step 1: Assign Static Local IP

### Option A: Static IP in Windows

1. **Open Network Settings**:
   ```powershell
   # Method 1: PowerShell
   ncpa.cpl
   
   # Method 2: Settings app
   ms-settings:network-ethernet
   ```

2. **Configure IPv4 Settings**:
   - Right-click your network adapter → Properties
   - Select "Internet Protocol Version 4 (TCP/IPv4)"
   - Click "Properties"

3. **Enter Static IP**:
   ```
   IP Address: 192.168.1.100  (choose unused IP in your range)
   Subnet Mask: 255.255.255.0
   Default Gateway: 192.168.1.1  (your router IP)
   Preferred DNS: 8.8.8.8  (Google DNS)
   Alternate DNS: 8.8.4.4
   ```

4. **Verify**:
   ```powershell
   ipconfig
   # Check that IPv4 Address matches your static IP
   ```

### Option B: DHCP Reservation in Router

1. Open router admin page
2. Find "DHCP Settings" or "Address Reservation"
3. Add reservation:
   - **MAC Address**: Your computer's MAC address
   - **IP Address**: 192.168.1.100 (or your choice)
   - **Description**: AI Voice Agent PC

4. **Save and reboot computer**

**Recommended**: Use Option B (DHCP Reservation) for easier management

---

## 🌐 Step 2: Find Your Router IP

```powershell
# Get default gateway (router IP)
ipconfig | Select-String "Default Gateway"

# Common router IPs:
# 192.168.1.1
# 192.168.0.1
# 10.0.0.1
# 192.168.1.254
```

**Save this IP** - you'll need it to access router admin.

---

## 🔐 Step 3: Access Router Admin Panel

### Common Router Access

1. **Open Browser**:
   ```
   http://192.168.1.1
   # or your router's IP
   ```

2. **Login with credentials**:
   - Check router label/sticker for default credentials
   - Common defaults:
     - admin / admin
     - admin / password
     - admin / (blank)
   - **Check router manual if default doesn't work**

### Router-Specific Access

**TP-Link**:
- URL: http://192.168.0.1 or http://tplinkwifi.net
- Default: admin / admin

**Netgear**:
- URL: http://192.168.1.1 or http://routerlogin.net
- Default: admin / password

**Linksys**:
- URL: http://192.168.1.1 or http://myrouter.local
- Default: admin / admin

**ASUS**:
- URL: http://192.168.1.1 or http://router.asus.com
- Default: admin / admin

**D-Link**:
- URL: http://192.168.0.1
- Default: admin / (blank)

---

## ⚙️ Step 4: Configure Port Forwarding

### General Steps (varies by router)

1. **Find Port Forwarding Section**:
   - Look for: "Port Forwarding", "Virtual Server", "NAT", or "Applications"
   - Usually under "Advanced" or "Security" tab

2. **Add New Rule**:
   
   **Rule Configuration**:
   ```
   Service Name: AI Voice Agent
   External Port/Start Port: 80
   Internal Port/End Port: 80
   Internal IP Address: 192.168.1.100  (your computer's static IP)
   Protocol: TCP
   Status/Enable: Enabled/Yes
   ```

3. **Save Settings**:
   - Click "Save", "Apply", or "Add"
   - Router may need to reboot

### Router-Specific Instructions

#### TP-Link

1. Navigate to: **Advanced → NAT Forwarding → Virtual Servers**
2. Click "Add"
3. Fill in:
   ```
   Service Type: Custom
   External Port: 80
   Internal IP: 192.168.1.100
   Internal Port: 80
   Protocol: TCP
   Status: Enabled
   ```
4. Click "Save"

#### Netgear

1. Navigate to: **Advanced → Advanced Setup → Port Forwarding/Port Triggering**
2. Select "Port Forwarding"
3. Click "Add Custom Service"
4. Fill in:
   ```
   Service Name: AI_Voice_Agent
   Service Type: TCP
   External Starting Port: 80
   External Ending Port: 80
   Internal Starting Port: 80
   Internal Ending Port: 80
   Internal IP Address: 192.168.1.100
   ```
5. Click "Apply"

#### Linksys

1. Navigate to: **Security → Apps and Gaming → Single Port Forwarding**
2. Fill in:
   ```
   Application Name: AI Voice Agent
   External Port: 80
   Internal Port: 80
   Protocol: TCP
   Device IP: 192.168.1.100
   Enabled: Yes
   ```
3. Click "Save Settings"

#### ASUS

1. Navigate to: **WAN → Virtual Server/Port Forwarding**
2. Enable "Port Forwarding"
3. Add rule:
   ```
   Service Name: AI_Voice_Agent
   Port Range: 80
   Local IP: 192.168.1.100
   Local Port: 80
   Protocol: TCP
   ```
4. Click "Apply"

---

## 🌍 Step 5: Find Your Public IP

Your public IP is how others will access your service from the internet.

### Method 1: PowerShell
```powershell
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

### Method 2: Web Browser
Visit any of these:
- https://whatismyipaddress.com/
- https://www.whatismyip.com/
- https://ipinfo.io/ip

### Method 3: Router Admin Panel
- Most routers show public IP on the main dashboard
- Look for "WAN IP", "External IP", or "Internet IP"

**Note**: Your public IP may change if you don't have a static IP from your ISP. See "Dynamic DNS" section below.

---

## ✅ Step 6: Test Port Forwarding

### Internal Testing

1. **Test from another device on your network**:
   ```
   http://192.168.1.100
   # Should show AI Voice Agent interface
   ```

### External Testing

1. **Use mobile data** (disconnect from WiFi):
   ```
   http://YOUR_PUBLIC_IP
   # Should show AI Voice Agent interface
   ```

2. **Use online port checker**:
   - Visit: https://www.yougetsignal.com/tools/open-ports/
   - Enter your public IP and port 80
   - Click "Check"
   - Should show: "Port 80 is open"

3. **Use PowerShell** (from another network):
   ```powershell
   Test-NetConnection -ComputerName YOUR_PUBLIC_IP -Port 80
   
   # Should show: TcpTestSucceeded : True
   ```

---

## 🔄 Dynamic DNS Setup (Optional but Recommended)

If your ISP changes your public IP regularly, use Dynamic DNS (DDNS).

### Why Use DDNS?

- Your public IP changes → your domain stays the same
- Access via: `myvoiceagent.ddns.net` instead of changing IP
- Easier to remember and share

### Popular Free DDNS Providers

1. **No-IP** (https://www.noip.com/)
   - Free subdomain: yourusername.ddns.net
   - 1 hostname free

2. **DuckDNS** (https://www.duckdns.org/)
   - Free subdomains: yourusername.duckdns.org
   - Unlimited

3. **Dynu** (https://www.dynu.com/)
   - Free subdomain
   - Multiple options

### Setup Process (Example: No-IP)

1. **Create Account**:
   - Visit: https://www.noip.com/sign-up
   - Register free account

2. **Create Hostname**:
   - Login to dashboard
   - Click "Dynamic DNS" → "Create Hostname"
   - Choose hostname: `myvoiceagent.ddns.net`
   - Type: DNS Host (A)
   - IP: (will auto-detect your public IP)
   - Click "Create Hostname"

3. **Install DDNS Client**:
   ```powershell
   # Download No-IP DUC (Dynamic Update Client)
   # From: https://www.noip.com/download
   ```

4. **Configure Client**:
   - Install and run No-IP DUC
   - Login with your No-IP credentials
   - Select hostname to update
   - Client will auto-update IP when it changes

5. **Test**:
   ```
   http://myvoiceagent.ddns.net
   # Should access your AI Voice Agent
   ```

---

## 🔒 Security Considerations

### Essential Security Measures

1. **Use Strong Authentication**:
   ```python
   # Add to backend.py
   from fastapi.security import HTTPBasic, HTTPBasicCredentials
   
   security = HTTPBasic()
   
   @app.get("/")
   async def root(credentials: HTTPBasicCredentials = Depends(security)):
       # Add authentication logic
   ```

2. **Enable HTTPS/TLS**:
   - Get free SSL certificate from Let's Encrypt
   - Configure nginx for HTTPS
   - Redirect HTTP to HTTPS

3. **Implement Rate Limiting**:
   ```python
   # Already in SECURITY_CHECKLIST.md
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

4. **Use Firewall Rules**:
   ```powershell
   # Only allow specific countries (example)
   # Requires advanced firewall or third-party tool
   ```

5. **Monitor Access Logs**:
   ```powershell
   # Check nginx access logs regularly
   Get-Content C:\nginx\logs\access.log -Tail 50
   ```

### IP Whitelisting (Optional)

Only allow specific IPs to access:

1. **In nginx.conf**:
   ```nginx
   server {
       listen 80;
       
       # Allow specific IPs
       allow 1.2.3.4;        # Friend's IP
       allow 5.6.7.0/24;     # Office network
       deny all;             # Deny everyone else
       
       # ... rest of config
   }
   ```

2. **Reload nginx**:
   ```powershell
   cd C:\nginx
   .\nginx.exe -s reload
   ```

### Regular Maintenance

- [ ] Update Windows regularly
- [ ] Update Python packages monthly
- [ ] Review access logs weekly
- [ ] Change router admin password
- [ ] Monitor for unusual activity
- [ ] Backup configuration files

---

## 🚨 Troubleshooting

### Port Forwarding Not Working

**Issue**: External access fails, internal works

**Checklist**:
1. ✅ Static IP configured correctly?
   ```powershell
   ipconfig | Select-String "IPv4"
   ```

2. ✅ Port forwarding rule saved in router?
   - Re-check router settings
   - Verify internal IP matches

3. ✅ Router rebooted after configuration?
   ```powershell
   # Reboot router via admin panel or power cycle
   ```

4. ✅ ISP blocking port 80?
   - Some ISPs block port 80
   - Try alternative port (8080, 8888)
   - Update nginx to listen on alternative port

5. ✅ Windows Firewall allows port 80?
   ```powershell
   Get-NetFirewallRule -DisplayName "AI Voice Agent*"
   ```

6. ✅ Computer actually running on static IP?
   ```powershell
   ipconfig /all
   # Check "DHCP Enabled: No"
   ```

### ISP Blocks Port 80

Many ISPs block port 80 for residential connections.

**Solution**:

1. **Use alternative port**:
   ```nginx
   # In nginx.conf
   server {
       listen 8080;  # Instead of 80
   }
   ```

2. **Update port forwarding**:
   ```
   External Port: 8080
   Internal Port: 80
   ```

3. **Access via**:
   ```
   http://YOUR_PUBLIC_IP:8080
   ```

### Double NAT Issue

**Symptom**: Port forwarding configured but doesn't work

**Cause**: Your router is behind another router (ISP modem/router combo)

**Solution**:
1. **Check for double NAT**:
   - If router WAN IP is 192.168.x.x or 10.x.x.x → Double NAT exists
   
2. **Fix**:
   - Put ISP router in "bridge mode" or "passthrough mode"
   - OR configure port forwarding on BOTH routers
   - Contact ISP if needed

### CG-NAT (Carrier-Grade NAT)

**Symptom**: Port forwarding works internally but not externally

**Cause**: ISP uses CG-NAT (shared public IP)

**Check**:
- If router WAN IP doesn't match your public IP → CG-NAT

**Solution**:
- Request public IP from ISP (may cost extra)
- OR use VPN with port forwarding (like ZeroTier, Tailscale)
- OR use reverse proxy service (ngrok, Cloudflare Tunnel)

---

## 🌐 Alternative: Cloudflare Tunnel

If port forwarding doesn't work (CG-NAT, ISP blocks), use Cloudflare Tunnel.

### Advantages
- No port forwarding needed
- Free SSL/TLS
- DDoS protection
- Works behind any firewall

### Setup

1. **Install cloudflared**:
   ```powershell
   # Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
   ```

2. **Authenticate**:
   ```powershell
   cloudflared tunnel login
   ```

3. **Create tunnel**:
   ```powershell
   cloudflared tunnel create ai-voice-agent
   ```

4. **Configure tunnel**:
   ```yaml
   # Create: C:\cloudflared\config.yml
   tunnel: ai-voice-agent
   credentials-file: C:\Users\YourUser\.cloudflared\UUID.json
   
   ingress:
     - hostname: ai-voice-agent.yourdomain.com
       service: http://localhost:80
     - service: http_status:404
   ```

5. **Run tunnel**:
   ```powershell
   cloudflared tunnel run ai-voice-agent
   ```

6. **Access via**:
   ```
   https://ai-voice-agent.yourdomain.com
   ```

---

## 📊 Port Forwarding Checklist

Before contacting support, verify:

- [ ] Static local IP assigned (192.168.x.x)
- [ ] Port forwarding rule created in router
- [ ] Rule points to correct internal IP
- [ ] Protocol set to TCP
- [ ] Router rebooted after changes
- [ ] Windows Firewall allows port 80
- [ ] AI Voice Agent services running
- [ ] Internal access works (http://localhost)
- [ ] No double NAT (check router WAN IP)
- [ ] ISP doesn't block port 80
- [ ] External test from mobile data
- [ ] Port checker confirms port is open

---

## 📞 Getting Help

If port forwarding still doesn't work:

1. **Check router manual**: Search "YOUR_ROUTER_MODEL port forwarding"
2. **ISP support**: Ask if they block ports or use CG-NAT
3. **Router forums**: Search for your specific model
4. **Alternative solutions**: Consider Cloudflare Tunnel or VPN

---

## ⚠️ Legal Notice

- Check your ISP's Terms of Service
- Some ISPs prohibit running servers on residential connections
- Ensure compliance with local laws regarding data processing
- Consider privacy implications of exposing services

---

**Last Updated**: Document creation date  
**Next Review**: When changing ISP or router
