"""
Generate realistic, high-resolution dark-mode screenshot mockups of the CyberShield AI platform.
Saves PNG files into docs/screenshots/.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Theme Palette (Tailwind Dark Theme)
BG_MAIN = (15, 23, 42)      # slate-900
BG_SIDEBAR = (2, 6, 23)     # slate-950
BG_CARD = (30, 41, 59)      # slate-800
BG_CARD_HOVER = (51, 65, 85)# slate-700
BORDER_COLOR = (51, 65, 85) # slate-700
TEXT_WHITE = (248, 250, 252)# slate-50
TEXT_MUTED = (148, 163, 184)# slate-400
ACCENT_CYAN = (6, 182, 212) # cyan-500
ACCENT_BLUE = (59, 130, 246)# blue-500
COLOR_GREEN = (34, 197, 94) # emerald-500
COLOR_RED = (239, 68, 68)   # red-500
COLOR_YELLOW = (234, 179, 8)# amber-500
COLOR_ORANGE = (249, 115, 22)# orange-500

WIDTH = 1280
HEIGHT = 800

def get_font(size):
    try:
        # Try standard Windows system fonts
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

FONT_HEADER = get_font(22)
FONT_SUBHEADER = get_font(16)
FONT_BODY = get_font(13)
FONT_SMALL = get_font(11)
FONT_METRIC = get_font(32)

def draw_topbar(draw, title="CyberShield AI"):
    # TopBar
    draw.rectangle([240, 0, WIDTH, 60], fill=BG_SIDEBAR)
    draw.line([240, 60, WIDTH, 60], fill=BORDER_COLOR, width=1)
    draw.text((270, 18), title, font=FONT_SUBHEADER, fill=TEXT_WHITE)
    
    # Live Status & Notification Bell
    draw.ellipse([WIDTH - 180, 20, WIDTH - 160, 40], fill=BG_CARD)
    draw.text((WIDTH - 173, 23), "🔔", font=FONT_BODY, fill=ACCENT_CYAN)
    draw.ellipse([WIDTH - 165, 17, WIDTH - 153, 29], fill=COLOR_RED)
    draw.text((WIDTH - 161, 17), "3", font=FONT_SMALL, fill=TEXT_WHITE)
    
    # User Profile Pill
    draw.rounded_rectangle([WIDTH - 140, 14, WIDTH - 20, 46], radius=16, fill=BG_CARD)
    draw.ellipse([WIDTH - 135, 19, WIDTH - 113, 41], fill=ACCENT_BLUE)
    draw.text((WIDTH - 128, 23), "A", font=FONT_SMALL, fill=TEXT_WHITE)
    draw.text((WIDTH - 105, 23), "admin@cybershield", font=FONT_SMALL, fill=TEXT_MUTED)

def draw_sidebar(draw, active_item="Dashboard"):
    # Sidebar
    draw.rectangle([0, 0, 240, HEIGHT], fill=BG_SIDEBAR)
    draw.line([240, 0, 240, HEIGHT], fill=BORDER_COLOR, width=1)
    
    # Brand
    draw.rounded_rectangle([20, 16, 50, 46], radius=6, fill=ACCENT_CYAN)
    draw.text((27, 20), "🛡️", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    draw.text((60, 20), "CyberShield AI", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    draw.text((60, 40), "v1.0.0 Enterprise", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.line([15, 60, 225, 60], fill=BORDER_COLOR, width=1)
    
    # Navigation Items
    items = [
        "Dashboard", "Devices", "Agents", "Network Monitoring",
        "Vulnerability Mgmt", "Log Management", "Threat Detection",
        "Alerts & Incidents", "Threat Intelligence", "Reports",
        "AI Assistant", "Settings & Audit"
    ]
    
    y = 80
    for item in items:
        if item == active_item:
            draw.rounded_rectangle([15, y, 225, y + 36], radius=6, fill=BG_CARD)
            draw.text((35, y + 9), item, font=FONT_BODY, fill=ACCENT_CYAN)
        else:
            draw.text((35, y + 9), item, font=FONT_BODY, fill=TEXT_MUTED)
        y += 42

def make_login_page():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(img)
    
    # Login Card in center
    cx, cy = WIDTH // 2, HEIGHT // 2
    w, h = 420, 500
    x1, y1 = cx - w // 2, cy - h // 2
    x2, y2 = cx + w // 2, cy + h // 2
    
    draw.rounded_rectangle([x1, y1, x2, y2], radius=12, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    
    # Brand Header
    draw.rounded_rectangle([cx - 25, y1 + 30, cx + 25, y1 + 80], radius=10, fill=ACCENT_CYAN)
    draw.text((cx - 15, y1 + 40), "🛡️", font=FONT_HEADER, fill=TEXT_WHITE)
    
    draw.text((cx - 85, y1 + 95), "CyberShield AI", font=FONT_HEADER, fill=TEXT_WHITE)
    draw.text((cx - 130, y1 + 130), "Unified Cybersecurity & Threat Monitoring", font=FONT_SMALL, fill=TEXT_MUTED)
    
    # Form Fields
    # Email
    draw.text((x1 + 35, y1 + 170), "Corporate Email", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.rounded_rectangle([x1 + 35, y1 + 190, x2 - 35, y1 + 230], radius=6, fill=BG_MAIN, outline=BORDER_COLOR, width=1)
    draw.text((x1 + 45, y1 + 202), "admin@cybershield.ai", font=FONT_BODY, fill=TEXT_WHITE)
    
    # Password
    draw.text((x1 + 35, y1 + 245), "Password", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.rounded_rectangle([x1 + 35, y1 + 265, x2 - 35, y1 + 305], radius=6, fill=BG_MAIN, outline=BORDER_COLOR, width=1)
    draw.text((x1 + 45, y1 + 277), "••••••••••••••••••••", font=FONT_BODY, fill=TEXT_WHITE)
    
    # Rate limiting badge
    draw.text((x1 + 35, y1 + 320), "🔒 Protected by SlowAPI Rate Limiting (10 req/min)", font=FONT_SMALL, fill=ACCENT_CYAN)
    
    # Login Button
    draw.rounded_rectangle([x1 + 35, y1 + 355, x2 - 35, y1 + 400], radius=6, fill=ACCENT_BLUE)
    draw.text((cx - 30, y1 + 368), "Sign In", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    
    # Footer Notice
    draw.text((cx - 110, y1 + 430), "Role-Based Access Control (Admin / Analyst / Viewer)", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.text((cx - 95, y1 + 450), "LocalRuleAI Security Engine • Neon PostgreSQL", font=FONT_SMALL, fill=TEXT_MUTED)
    
    img.save(os.path.join(OUTPUT_DIR, "login_page.png"))

def make_dashboard():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(img)
    draw_sidebar(draw, "Dashboard")
    draw_topbar(draw, "Security Operations Dashboard")
    
    # 4 Metric Cards
    metrics = [
        ("Active Agents", "1 Online", COLOR_GREEN, "100% Reachable"),
        ("Discovered Devices", "12 Hosts", ACCENT_CYAN, "3 High Exposure"),
        ("Open Vulnerabilities", "18 CVEs", COLOR_ORANGE, "4 Critical CVSS >= 9.0"),
        ("Active Alerts", "6 Open", COLOR_RED, "2 Brute Force Incidents")
    ]
    
    for i, (label, val, color, sub) in enumerate(metrics):
        x = 270 + i * 245
        draw.rounded_rectangle([x, 80, x + 230, 180], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
        draw.text((x + 15, 95), label, font=FONT_SMALL, fill=TEXT_MUTED)
        draw.text((x + 15, 115), val, font=FONT_METRIC, fill=color)
        draw.text((x + 15, 155), sub, font=FONT_SMALL, fill=TEXT_MUTED)
        
    # Chart area: Threat Severity Distribution & System Telemetry
    draw.rounded_rectangle([270, 200, 750, 430], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    draw.text((290, 215), "Incident Severity & Threat Trends", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    # Mock visual chart lines/bars
    draw.line([300, 400, 720, 400], fill=BORDER_COLOR, width=2)
    # Severity bars
    draw.rectangle([340, 280, 400, 400], fill=COLOR_RED)
    draw.text((350, 405), "Critical", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.rectangle([440, 250, 500, 400], fill=COLOR_ORANGE)
    draw.text((455, 405), "High", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.rectangle([540, 310, 600, 400], fill=COLOR_YELLOW)
    draw.text((550, 405), "Medium", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.rectangle([640, 350, 700, 400], fill=COLOR_GREEN)
    draw.text((655, 405), "Low", font=FONT_SMALL, fill=TEXT_MUTED)
    
    # System Status Panel
    draw.rounded_rectangle([770, 200, 1240, 430], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    draw.text((790, 215), "Agent Telemetry & Sensor Health", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    draw.text((790, 250), "Sensor: primary-network-sensor", font=FONT_BODY, fill=ACCENT_CYAN)
    draw.text((790, 280), "CPU Utilization: 18.4% (Normal)", font=FONT_BODY, fill=TEXT_MUTED)
    draw.rounded_rectangle([790, 305, 1200, 315], radius=4, fill=BG_MAIN)
    draw.rounded_rectangle([790, 305, 870, 315], radius=4, fill=COLOR_GREEN)
    
    draw.text((790, 335), "RAM Utilization: 54.2% (Bounded)", font=FONT_BODY, fill=TEXT_MUTED)
    draw.rounded_rectangle([790, 360, 1200, 370], radius=4, fill=BG_MAIN)
    draw.rounded_rectangle([790, 360, 1010, 370], radius=4, fill=ACCENT_BLUE)
    draw.text((790, 390), "Heartbeat: Every 30s • Auto-refresh 60s active", font=FONT_SMALL, fill=COLOR_GREEN)

    # Recent Alerts Table
    draw.rounded_rectangle([270, 450, 1240, 770], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    draw.text((290, 465), "Recent Security Incidents & Threat Detections", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    
    headers = [("TIME", 290), ("TYPE", 410), ("SEVERITY", 560), ("SOURCE IP", 670), ("DESCRIPTION", 800), ("STATUS", 1120)]
    for h, px in headers:
        draw.text((px, 500), h, font=FONT_SMALL, fill=TEXT_MUTED)
    draw.line([285, 520, 1225, 520], fill=BORDER_COLOR, width=1)
    
    rows = [
        ("2 mins ago", "brute_force", "High", "192.168.1.105", "5 failed logins within 10 min window", "Open"),
        ("14 mins ago", "port_scan", "Medium", "192.168.1.42", "15 open ports scanned on web-srv-01", "Acknowledged"),
        ("1 hr ago", "malware_indicator", "High", "203.0.113.19", "Source IP matched Threat Intelligence IOC", "Investigating"),
        ("3 hrs ago", "suspicious_login", "Medium", "192.168.1.200", "Successful login following multiple failures", "Resolved"),
    ]
    
    for idx, (t, typ, sev, ip, desc, st) in enumerate(rows):
        ry = 535 + idx * 45
        draw.text((290, ry), t, font=FONT_BODY, fill=TEXT_MUTED)
        draw.text((410, ry), typ, font=FONT_BODY, fill=ACCENT_CYAN)
        
        # Severity Badge
        s_color = COLOR_RED if sev == "High" else (COLOR_ORANGE if sev == "Medium" else COLOR_GREEN)
        draw.rounded_rectangle([555, ry - 3, 630, ry + 18], radius=4, fill=s_color)
        draw.text((565, ry), sev, font=FONT_SMALL, fill=TEXT_WHITE)
        
        draw.text((670, ry), ip, font=FONT_BODY, fill=TEXT_WHITE)
        draw.text((800, ry), desc[:40], font=FONT_BODY, fill=TEXT_MUTED)
        
        # Status Badge
        draw.rounded_rectangle([1115, ry - 3, 1215, ry + 18], radius=4, fill=BG_MAIN, outline=BORDER_COLOR)
        draw.text((1125, ry), st, font=FONT_SMALL, fill=TEXT_WHITE)
        draw.line([285, ry + 30, 1225, ry + 30], fill=BORDER_COLOR, width=1)
        
    img.save(os.path.join(OUTPUT_DIR, "dashboard.png"))

def make_agents_page():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(img)
    draw_sidebar(draw, "Agents")
    draw_topbar(draw, "Sensor Agent Management")
    
    # Header & Action Button
    draw.text((270, 80), "Connected Monitoring Agents", font=FONT_HEADER, fill=TEXT_WHITE)
    draw.text((270, 110), "Manage endpoint sensors, telemetry heartbeats, and credential tokens", font=FONT_SMALL, fill=TEXT_MUTED)
    
    draw.rounded_rectangle([1080, 85, 1240, 125], radius=6, fill=ACCENT_BLUE)
    draw.text((1095, 96), "+ Generate Token", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    
    # Agents Table
    draw.rounded_rectangle([270, 150, 1240, 750], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    
    headers = [("NAME", 290), ("HOSTNAME", 440), ("STATUS", 580), ("VERSION", 680), ("CPU / RAM", 780), ("LAST HEARTBEAT", 920), ("ACTIONS", 1120)]
    for h, px in headers:
        draw.text((px, 170), h, font=FONT_SMALL, fill=TEXT_MUTED)
    draw.line([285, 195, 1225, 195], fill=BORDER_COLOR, width=1)
    
    # Active Agent Row
    draw.text((290, 215), "primary-sensor-hq", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((440, 215), "DESKTOP-SEC-NODE", font=FONT_BODY, fill=TEXT_MUTED)
    
    draw.rounded_rectangle([575, 212, 645, 233], radius=4, fill=COLOR_GREEN)
    draw.text((585, 215), "ONLINE", font=FONT_SMALL, fill=TEXT_WHITE)
    
    draw.text((680, 215), "v1.0.0", font=FONT_BODY, fill=TEXT_MUTED)
    draw.text((780, 215), "18.4% / 54.2%", font=FONT_BODY, fill=TEXT_MUTED)
    draw.text((920, 215), "2026-10-14 21:50:12", font=FONT_BODY, fill=TEXT_MUTED)
    
    draw.rounded_rectangle([1110, 210, 1170, 235], radius=4, fill=BG_MAIN, outline=BORDER_COLOR)
    draw.text((1122, 215), "Rotate", font=FONT_SMALL, fill=ACCENT_CYAN)
    
    draw.rounded_rectangle([1180, 210, 1230, 235], radius=4, fill=COLOR_RED)
    draw.text((1188, 215), "Revoke", font=FONT_SMALL, fill=TEXT_WHITE)
    
    draw.line([285, 255, 1225, 255], fill=BORDER_COLOR, width=1)
    
    # Agent Heartbeat Metrics Graphic
    draw.text((290, 290), "Detailed Telemetry Stream: primary-sensor-hq", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    draw.rounded_rectangle([290, 330, 740, 500], radius=6, fill=BG_MAIN, outline=BORDER_COLOR)
    draw.text((310, 350), "• OS: Windows 11 Enterprise (Build 22631)", font=FONT_BODY, fill=TEXT_MUTED)
    draw.text((310, 380), "• IP Address: 192.168.1.15 (Subnet: 192.168.1.0/24)", font=FONT_BODY, fill=TEXT_MUTED)
    draw.text((310, 410), "• Task Polling: GET /agents/tasks (Interval: 30s)", font=FONT_BODY, fill=TEXT_MUTED)
    draw.text((310, 440), "• Offline Threshold: 90s (3 consecutive missed heartbeats)", font=FONT_BODY, fill=TEXT_MUTED)
    draw.text((310, 470), "• Identity Store: agent_identity.json (chmod 0600)", font=FONT_BODY, fill=COLOR_GREEN)
    
    # Generated Token Dialog Mockup
    draw.rounded_rectangle([780, 330, 1210, 500], radius=6, fill=BG_MAIN, outline=BORDER_COLOR)
    draw.text((800, 350), "Single-Use Enrollment Token Generator", font=FONT_SUBHEADER, fill=ACCENT_CYAN)
    draw.text((800, 385), "One-time registration token valid for 60 minutes:", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.rounded_rectangle([800, 410, 1190, 445], radius=4, fill=BG_CARD)
    draw.text((815, 420), "cshld_enroll_8f3a9e2d1c7b04e5f992a...", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((800, 465), "SHA-256 hashed on storage • Zero plaintext logging", font=FONT_SMALL, fill=TEXT_MUTED)

    img.save(os.path.join(OUTPUT_DIR, "agents_page.png"))

def make_devices_page():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(img)
    draw_sidebar(draw, "Devices")
    draw_topbar(draw, "Discovered Network Assets")
    
    draw.text((270, 80), "Discovered Devices & Asset Inventory", font=FONT_HEADER, fill=TEXT_WHITE)
    draw.text((270, 110), "Automated Nmap ping sweep & ARP table device correlation", font=FONT_SMALL, fill=TEXT_MUTED)
    
    draw.rounded_rectangle([1040, 85, 1240, 125], radius=6, fill=ACCENT_BLUE)
    draw.text((1055, 96), "▶ Run Discovery Scan", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    
    # Devices Table
    draw.rounded_rectangle([270, 150, 1240, 750], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    
    headers = [("IP ADDRESS", 290), ("MAC / VENDOR", 430), ("HOSTNAME", 600), ("OPERATING SYSTEM", 750), ("STATUS", 920), ("RISK BAND", 1020), ("DETAILS", 1140)]
    for h, px in headers:
        draw.text((px, 170), h, font=FONT_SMALL, fill=TEXT_MUTED)
    draw.line([285, 195, 1225, 195], fill=BORDER_COLOR, width=1)
    
    devices = [
        ("192.168.1.1", "00:50:56:C0:00:01 (Cisco)", "gw-core-router", "Cisco IOS-XE 17.3", "online", "Low (12)", COLOR_GREEN),
        ("192.168.1.10", "BC:24:11:92:AA:04 (Dell)", "srv-prod-db01", "Ubuntu 22.04 LTS", "online", "Critical (82)", COLOR_RED),
        ("192.168.1.42", "00:1A:2B:3C:4D:5E (HP)", "srv-web-nginx", "Debian GNU/Linux 11", "online", "High (65)", COLOR_ORANGE),
        ("192.168.1.105", "3C:D9:2B:77:81:F2 (Apple)", "macbook-jdoe", "macOS Sonoma 14.4", "online", "Medium (38)", COLOR_YELLOW),
        ("192.168.1.200", "52:54:00:12:34:56 (Intel)", "corp-nas-storage", "Synology DSM 7.1", "offline", "Low (15)", COLOR_GREEN),
    ]
    
    for idx, (ip, mac, host, os_name, st, risk, r_color) in enumerate(devices):
        ry = 215 + idx * 55
        draw.text((290, ry), ip, font=FONT_BODY, fill=ACCENT_CYAN)
        draw.text((430, ry), mac, font=FONT_BODY, fill=TEXT_MUTED)
        draw.text((600, ry), host, font=FONT_BODY, fill=TEXT_WHITE)
        draw.text((750, ry), os_name, font=FONT_BODY, fill=TEXT_MUTED)
        
        # Status
        s_bg = COLOR_GREEN if st == "online" else TEXT_MUTED
        draw.rounded_rectangle([915, ry - 3, 975, ry + 18], radius=4, fill=s_bg)
        draw.text((925, ry), st, font=FONT_SMALL, fill=TEXT_WHITE)
        
        # Risk Band
        draw.rounded_rectangle([1015, ry - 3, 1105, ry + 18], radius=4, fill=r_color)
        draw.text((1025, ry), risk, font=FONT_SMALL, fill=TEXT_WHITE)
        
        draw.rounded_rectangle([1135, ry - 3, 1205, ry + 18], radius=4, fill=BG_MAIN, outline=BORDER_COLOR)
        draw.text((1145, ry), "View Asset", font=FONT_SMALL, fill=ACCENT_CYAN)
        
        draw.line([285, ry + 35, 1225, ry + 35], fill=BORDER_COLOR, width=1)
        
    img.save(os.path.join(OUTPUT_DIR, "devices_page.png"))

def make_vulnerabilities_page():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(img)
    draw_sidebar(draw, "Vulnerability Mgmt")
    draw_topbar(draw, "Vulnerability Assessment & CVE Database")
    
    draw.text((270, 80), "Detected Vulnerabilities & CVE Correlation", font=FONT_HEADER, fill=TEXT_WHITE)
    draw.text((270, 110), "Service-version mapping via Nmap -sV banner grabbing", font=FONT_SMALL, fill=TEXT_MUTED)
    
    # Vulnerabilities Table
    draw.rounded_rectangle([270, 150, 1240, 750], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    
    headers = [("CVE ID", 290), ("SEVERITY", 410), ("CVSS", 490), ("AFFECTED SERVICE", 560), ("HOST IP", 730), ("VULNERABILITY SUMMARY", 860), ("AI ACTION", 1120)]
    for h, px in headers:
        draw.text((px, 170), h, font=FONT_SMALL, fill=TEXT_MUTED)
    draw.line([285, 195, 1225, 195], fill=BORDER_COLOR, width=1)
    
    vulns = [
        ("CVE-2021-41773", "Critical", "9.8", "Apache 2.4.49", "192.168.1.42", "Path traversal and remote code execution in Apache", COLOR_RED),
        ("CVE-2023-48795", "High", "7.5", "OpenSSH 8.2p1", "192.168.1.10", "Terrapin attack: prefix truncation in SSH protocol", COLOR_ORANGE),
        ("CVE-2021-44228", "Critical", "10.0", "Log4j 2.14.1", "192.168.1.10", "Log4Shell JNDI injection remote code execution", COLOR_RED),
        ("CVE-2020-0601", "High", "8.1", "CryptoAPI", "192.168.1.15", "Windows CryptoAPI spoofing vulnerability", COLOR_ORANGE),
        ("CVE-2022-22965", "Critical", "9.8", "Spring Framework", "192.168.1.42", "Spring4Shell remote code execution via DataBinder", COLOR_RED),
    ]
    
    for idx, (cve, sev, score, svc, ip, sumry, s_color) in enumerate(vulns):
        ry = 215 + idx * 55
        draw.text((290, ry), cve, font=FONT_BODY, fill=ACCENT_CYAN)
        
        draw.rounded_rectangle([405, ry - 3, 470, ry + 18], radius=4, fill=s_color)
        draw.text((415, ry), sev, font=FONT_SMALL, fill=TEXT_WHITE)
        
        draw.text((495, ry), score, font=FONT_BODY, fill=TEXT_WHITE)
        draw.text((560, ry), svc, font=FONT_BODY, fill=TEXT_MUTED)
        draw.text((730, ry), ip, font=FONT_BODY, fill=ACCENT_BLUE)
        draw.text((860, ry), sumry[:32] + "...", font=FONT_BODY, fill=TEXT_MUTED)
        
        draw.rounded_rectangle([1110, ry - 3, 1220, ry + 18], radius=4, fill=BG_MAIN, outline=ACCENT_CYAN)
        draw.text((1118, ry), "🤖 Explain with AI", font=FONT_SMALL, fill=ACCENT_CYAN)
        
        draw.line([285, ry + 35, 1225, ry + 35], fill=BORDER_COLOR, width=1)
        
    img.save(os.path.join(OUTPUT_DIR, "vulnerabilities_page.png"))

def make_alerts_page():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(img)
    draw_sidebar(draw, "Alerts & Incidents")
    draw_topbar(draw, "Security Incident Triage Board")
    
    draw.text((270, 80), "Security Alerts & Incident Lifecycle Management", font=FONT_HEADER, fill=TEXT_WHITE)
    draw.text((270, 110), "Filter by status and advance lifecycle: Open → Acknowledged → Investigating → Resolved", font=FONT_SMALL, fill=TEXT_MUTED)
    
    # Status Tabs
    tabs = [("All (24)", False), ("Open (6)", True), ("Acknowledged (4)", False), ("Investigating (3)", False), ("Resolved (11)", False)]
    for i, (tab, is_active) in enumerate(tabs):
        tx = 270 + i * 140
        if is_active:
            draw.rounded_rectangle([tx, 140, tx + 130, 170], radius=6, fill=ACCENT_BLUE)
            draw.text((tx + 15, 148), tab, font=FONT_SMALL, fill=TEXT_WHITE)
        else:
            draw.rounded_rectangle([tx, 140, tx + 130, 170], radius=6, fill=BG_CARD)
            draw.text((tx + 15, 148), tab, font=FONT_SMALL, fill=TEXT_MUTED)
            
    # Incident Card
    draw.rounded_rectangle([270, 190, 1240, 480], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    draw.text((290, 205), "Incident #ALT-2026-0914: Brute Force Authentication Attack", font=FONT_SUBHEADER, fill=COLOR_RED)
    
    draw.text((290, 240), "Rule Triggered: 5+ failed logins from same source IP within 10 minutes", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((290, 270), "Affected Device: srv-web-nginx (192.168.1.42) • Attacker IP: 198.51.100.44", font=FONT_BODY, fill=TEXT_MUTED)
    draw.text((290, 300), "Initial Risk Score: 40 • Detected: 2026-10-14 21:42:00 UTC", font=FONT_BODY, fill=TEXT_MUTED)
    draw.text((290, 330), "Current Lifecycle Status: OPEN", font=FONT_BODY, fill=COLOR_RED)
    
    # Action Buttons
    draw.rounded_rectangle([290, 370, 420, 405], radius=6, fill=COLOR_YELLOW)
    draw.text((305, 380), "Acknowledge", font=FONT_SMALL, fill=BG_MAIN)
    
    draw.rounded_rectangle([435, 370, 560, 405], radius=6, fill=ACCENT_BLUE)
    draw.text((450, 380), "Investigate", font=FONT_SMALL, fill=TEXT_WHITE)
    
    draw.rounded_rectangle([575, 370, 690, 405], radius=6, fill=COLOR_GREEN)
    draw.text((595, 380), "Resolve", font=FONT_SMALL, fill=TEXT_WHITE)
    
    draw.rounded_rectangle([705, 370, 830, 405], radius=6, fill=BG_MAIN, outline=COLOR_RED)
    draw.text((715, 380), "False Positive", font=FONT_SMALL, fill=COLOR_RED)
    
    draw.rounded_rectangle([845, 370, 1010, 405], radius=6, fill=BG_MAIN, outline=ACCENT_CYAN)
    draw.text((858, 380), "🤖 Explain with AI", font=FONT_SMALL, fill=ACCENT_CYAN)
    
    # Audit History Timeline
    draw.line([290, 425, 1220, 425], fill=BORDER_COLOR, width=1)
    draw.text((290, 440), "Timeline: [21:42:00 UTC System Generated Alert] ➔ [21:44:15 UTC Analyst Assigned] ➔ Pending Triage", font=FONT_SMALL, fill=TEXT_MUTED)

    img.save(os.path.join(OUTPUT_DIR, "alerts_page.png"))

def make_ai_explanation():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(img)
    draw_sidebar(draw, "AI Assistant")
    draw_topbar(draw, "Local Security Explanation Engine")
    
    draw.text((270, 80), "Local Security Explanation Engine (LocalRuleAI)", font=FONT_HEADER, fill=TEXT_WHITE)
    draw.text((270, 110), "Deterministic, zero-exfiltration security reasoning powered entirely on-premise", font=FONT_SMALL, fill=COLOR_GREEN)
    
    # Explanation Panel
    draw.rounded_rectangle([270, 150, 1240, 750], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    
    # Banner Badge
    draw.rounded_rectangle([290, 170, 620, 205], radius=6, fill=BG_MAIN, outline=ACCENT_CYAN)
    draw.text((305, 180), "🛡️ 100% On-Premise Engine • Zero Cloud LLM APIs", font=FONT_SMALL, fill=ACCENT_CYAN)
    
    draw.text((290, 230), "Automated Root Cause Assessment: Brute Force Authentication", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    
    assessment_lines = [
        "1. Executive Summary:",
        "   The platform detection engine identified a distributed credential-stuffing attack originating from IP 198.51.100.44.",
        "   The host generated 5 authentication failures in under 10 minutes targeting root and admin accounts.",
        "",
        "2. MITRE ATT&CK Mapping:",
        "   • Tactic: Credential Access (TA0006)",
        "   • Technique: Brute Force: Password Guessing (T1110.001)",
        "",
        "3. Recommended Immediate Containment Steps:",
        "   a) Execute firewall null-route for source IP 198.51.100.44 on the primary gateway router.",
        "   b) Invalidate existing active JWT sessions for target account admin@cybershield.ai.",
        "   c) Verify whether any corresponding successful login occurred during the event window.",
        "",
        "4. Long-Term Hardening:",
        "   • Enforce multi-factor authentication (MFA) across all administrative access points.",
        "   • Reduce lockout window threshold in backend configuration to 3 failed attempts."
    ]
    
    y = 265
    for line in assessment_lines:
        color = ACCENT_CYAN if line.startswith(("1.", "2.", "3.", "4.")) else TEXT_MUTED
        draw.text((290, y), line, font=FONT_BODY, fill=color)
        y += 26
        
    # Chat Input Box
    draw.rounded_rectangle([290, 670, 1140, 720], radius=6, fill=BG_MAIN, outline=BORDER_COLOR)
    draw.text((310, 687), "Ask Local Security Engine about mitigation strategies, CVE impacts, or incident remediation...", font=FONT_BODY, fill=TEXT_MUTED)
    
    draw.rounded_rectangle([1155, 670, 1220, 720], radius=6, fill=ACCENT_BLUE)
    draw.text((1170, 687), "Send", font=FONT_BODY, fill=TEXT_WHITE)

    img.save(os.path.join(OUTPUT_DIR, "ai_explanation.png"))

def make_report_pdf():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(img)
    draw_sidebar(draw, "Reports")
    draw_topbar(draw, "Executive & Compliance Reports")
    
    draw.text((270, 80), "Generated Security & Compliance Reports", font=FONT_HEADER, fill=TEXT_WHITE)
    draw.text((270, 110), "Export print-ready PDF summaries and CSV data archives powered by fpdf2", font=FONT_SMALL, fill=TEXT_MUTED)
    
    draw.rounded_rectangle([1060, 85, 1240, 125], radius=6, fill=ACCENT_BLUE)
    draw.text((1075, 96), "+ Generate Report", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    
    # Reports Archive Table
    draw.rounded_rectangle([270, 150, 750, 750], radius=8, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    draw.text((290, 170), "Report Archive", font=FONT_SUBHEADER, fill=TEXT_WHITE)
    
    rep_rows = [
        ("Security Overview Q4", "security_overview", "2026-10-14", "READY"),
        ("Monthly Vulnerability Audit", "vulnerability", "2026-10-01", "READY"),
        ("Incident Response Summary", "alert", "2026-09-15", "READY"),
        ("Quarterly SOC Compliance", "security_overview", "2026-07-01", "READY"),
    ]
    
    for idx, (title, r_type, dt, st) in enumerate(rep_rows):
        ry = 210 + idx * 80
        draw.text((290, ry), title, font=FONT_BODY, fill=TEXT_WHITE)
        draw.text((290, ry + 22), f"Type: {r_type} • Generated: {dt}", font=FONT_SMALL, fill=TEXT_MUTED)
        
        draw.rounded_rectangle([530, ry + 5, 620, ry + 32], radius=4, fill=BG_MAIN, outline=ACCENT_CYAN)
        draw.text((540, ry + 10), "📥 PDF", font=FONT_SMALL, fill=ACCENT_CYAN)
        
        draw.rounded_rectangle([635, ry + 5, 725, ry + 32], radius=4, fill=BG_MAIN, outline=COLOR_GREEN)
        draw.text((645, ry + 10), "📊 CSV", font=FONT_SMALL, fill=COLOR_GREEN)
        draw.line([285, ry + 55, 735, ry + 55], fill=BORDER_COLOR, width=1)
        
    # PDF Document Preview Card on right
    draw.rounded_rectangle([770, 150, 1240, 750], radius=8, fill=(245, 245, 245)) # Paper white
    draw_pdf = ImageDraw.Draw(img)
    
    # PDF Header
    draw_pdf.rectangle([770, 150, 1240, 210], fill=(15, 23, 42)) # Dark header
    draw_pdf.text((800, 165), "CYBERSHIELD AI — EXECUTIVE SECURITY REPORT", font=FONT_SUBHEADER, fill=(255, 255, 255))
    draw_pdf.text((800, 190), "Confidential • Prepared for Organization: Default Security Org", font=FONT_SMALL, fill=(148, 163, 184))
    
    # PDF Body preview
    draw_pdf.text((800, 230), "1. Executive Posture Overview", font=FONT_SUBHEADER, fill=(15, 23, 42))
    draw_pdf.text((800, 260), "Report ID: rep_918274a1 • Generated: 2026-10-14 21:55 UTC", font=FONT_SMALL, fill=(100, 100, 100))
    
    # PDF Table
    draw_pdf.rectangle([800, 290, 1210, 410], fill=(255, 255, 255), outline=(200, 200, 200))
    draw_pdf.text((815, 305), "Metric Category", font=FONT_SMALL, fill=(50, 50, 50))
    draw_pdf.text((1050, 305), "Recorded Value", font=FONT_SMALL, fill=(50, 50, 50))
    draw_pdf.line([800, 325, 1210, 325], fill=(220, 220, 220))
    
    pdf_metrics = [
        ("Monitored Endpoints & Sensors", "1 Online (100%)"),
        ("Discovered Network Devices", "12 Active Hosts"),
        ("Total Identified Vulnerabilities", "18 Findings"),
        ("Critical Severity CVEs", "4 Findings (Immediate Action)")
    ]
    for idx, (cat, v) in enumerate(pdf_metrics):
        my = 335 + idx * 22
        draw_pdf.text((815, my), cat, font=FONT_SMALL, fill=(80, 80, 80))
        draw_pdf.text((1050, my), v, font=FONT_SMALL, fill=(15, 23, 42))
        
    draw_pdf.text((800, 435), "2. Incident Response & Threat Summary", font=FONT_SUBHEADER, fill=(15, 23, 42))
    draw_pdf.text((800, 465), "• Brute Force Incidents Mitigated: 2", font=FONT_SMALL, fill=(80, 80, 80))
    draw_pdf.text((800, 485), "• Malicious Indicator Matches: 1", font=FONT_SMALL, fill=(80, 80, 80))
    draw_pdf.text((800, 505), "• Mean Time to Acknowledge (MTTA): 4.2 minutes", font=FONT_SMALL, fill=(80, 80, 80))
    
    draw_pdf.text((800, 545), "3. Recommended Actions & Next Steps", font=FONT_SUBHEADER, fill=(15, 23, 42))
    draw_pdf.text((800, 575), "• Prioritize remediation of CVE-2021-41773 on host 192.168.1.42.", font=FONT_SMALL, fill=(80, 80, 80))
    draw_pdf.text((800, 595), "• Update OpenSSH packages to version 9.6p1 on web server fleet.", font=FONT_SMALL, fill=(80, 80, 80))
    
    img.save(os.path.join(OUTPUT_DIR, "report_pdf.png"))

if __name__ == "__main__":
    print("Generating screenshots...")
    make_login_page()
    make_dashboard()
    make_agents_page()
    make_devices_page()
    make_vulnerabilities_page()
    make_alerts_page()
    make_ai_explanation()
    make_report_pdf()
    print("All 8 screenshots generated successfully in docs/screenshots/")
