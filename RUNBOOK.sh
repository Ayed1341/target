#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
#  APEX_HUNTER — RUNBOOK
#  All commands for authorized bug bounty / legal security research ONLY
#  365 Tools | 375 Skills | 16 Phases | Claude claude-opus-4-8 AI Analysis
# ══════════════════════════════════════════════════════════════════════════════
# Usage: read this file, copy the command that fits your engagement, run it.
# Set your target:
TARGET="https://help.flynas.com"
OUTPUT="./results"
AI_KEY="${ANTHROPIC_API_KEY:-}"   # export ANTHROPIC_API_KEY=sk-ant-... first
# ──────────────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════════════════
# [1] FULL NUCLEAR SCAN — all 16 phases, AI analysis, max coverage
#     Use for: full-scope bug bounty engagement, no time pressure
#     Time estimate: 45–90 min per target
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/full_$(date +%Y%m%d_%H%M)" \
  --phases 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16 \
  --workers 10 \
  --rate 2.0 \
  --depth 3 \
  --timeout 20 \
  --ai-key "$AI_KEY"


# ══════════════════════════════════════════════════════════════════════════════
# [2] QUICK RECON — phases 1–6 only, passive + basic active
#     Use for: initial target triage, scope mapping, before deeper testing
#     Time estimate: 5–10 min per target
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/recon_$(date +%Y%m%d_%H%M)" \
  --phases 1,2,3,4,5,6 \
  --workers 8 \
  --rate 3.0 \
  --timeout 15


# ══════════════════════════════════════════════════════════════════════════════
# [3] BLACK TEAM FULL — phases 10–16 (all black/red team techniques)
#     Use for: deep exploitation after recon is complete
#     Prerequisite: run quick recon first (phase 1-6) to build profile
#     Time estimate: 30–60 min per target
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/blackteam_$(date +%Y%m%d_%H%M)" \
  --phases 10,11,12,13,14,15,16 \
  --workers 10 \
  --rate 1.5 \
  --timeout 25 \
  --ai-key "$AI_KEY"


# ══════════════════════════════════════════════════════════════════════════════
# [4] STEALTH / LOW-AND-SLOW — all phases, low rate, high timeout
#     Use for: WAF-protected targets, IDS/rate-limit evasion
#     Time estimate: 3–6 hours per target
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/stealth_$(date +%Y%m%d_%H%M)" \
  --phases 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16 \
  --workers 3 \
  --rate 0.5 \
  --depth 2 \
  --timeout 30 \
  --ai-key "$AI_KEY"


# ══════════════════════════════════════════════════════════════════════════════
# [5] PHASE 16 CHAIN ONLY — contextual state + WAF bypass + post-exploit
#     Use for: after other phases already ran and found RCE/SQLi/IDOR
#     This phase CHAINS prior findings — run AFTER phases 1-15
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/chain_$(date +%Y%m%d_%H%M)" \
  --phases 16 \
  --workers 5 \
  --rate 1.0 \
  --timeout 25


# ══════════════════════════════════════════════════════════════════════════════
# [6] AUTHENTICATION + BUSINESS LOGIC — phases 3,6,7,8,16
#     Use for: targets with login / API / user accounts
#     Covers: IDOR, BFLA, JWT, CSRF, session, auth bypass, multi-stage chain
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/auth_$(date +%Y%m%d_%H%M)" \
  --phases 3,6,7,8,16 \
  --workers 8 \
  --rate 2.0 \
  --timeout 20


# ══════════════════════════════════════════════════════════════════════════════
# [7] API + GRAPHQL FOCUS — phases 5,7,9,11,13,15
#     Use for: REST API / GraphQL targets, microservices
#     Covers: API mapping, GQL introspection, BFLA, IDOR, schema harvest
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/api_$(date +%Y%m%d_%H%M)" \
  --phases 5,7,9,11,13,15 \
  --workers 8 \
  --rate 2.0 \
  --timeout 20


# ══════════════════════════════════════════════════════════════════════════════
# [8] INJECTION FOCUS — phases 8,10,12,13,16
#     Use for: SQLi / CMDi / SSTI / XXE / Log4Shell / RCE targeting
#     Covers: all injection classes + WAF bypass + post-RCE mapping
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/injection_$(date +%Y%m%d_%H%M)" \
  --phases 8,10,12,13,16 \
  --workers 8 \
  --rate 1.5 \
  --timeout 25 \
  --ai-key "$AI_KEY"


# ══════════════════════════════════════════════════════════════════════════════
# [9] CLOUD / INFRASTRUCTURE — phases 5,12,13,14,15
#     Use for: AWS/Azure/GCP exposed assets, cloud misconfigs, SSRF→IMDS
#     Covers: S3, IMDS pivot, Azure Blob, GCP metadata, K8s, Docker API
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "$TARGET" \
  --output "$OUTPUT/cloud_$(date +%Y%m%d_%H%M)" \
  --phases 5,12,13,14,15 \
  --workers 8 \
  --rate 2.0 \
  --timeout 20


# ══════════════════════════════════════════════════════════════════════════════
# [10] MULTI-TARGET SCAN — same phase set across multiple targets
#      Use for: full program scope, multiple subdomains
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py \
  --target "https://help.flynas.com" \
  --target "https://api.flynas.com" \
  --target "https://www.flynas.com" \
  --output "$OUTPUT/multi_$(date +%Y%m%d_%H%M)" \
  --phases 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16 \
  --workers 10 \
  --rate 2.0 \
  --timeout 20 \
  --ai-key "$AI_KEY"


# ══════════════════════════════════════════════════════════════════════════════
# [11] VIEW SKILLS INDEX — print all 375 skills and exit
# ══════════════════════════════════════════════════════════════════════════════
python3 APEX_HUNTER.py --skills


# ══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT SETUP (run once before scanning)
# ══════════════════════════════════════════════════════════════════════════════
# Install optional dependencies for full feature set:
pip3 install anthropic requests aiohttp python-jwt

# Set Anthropic API key for AI analysis:
export ANTHROPIC_API_KEY="sk-ant-YOUR_KEY_HERE"

# Verify the script parses cleanly:
python3 -c "import ast; ast.parse(open('APEX_HUNTER.py').read()); print('OK')"


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT STRUCTURE (per run)
# ══════════════════════════════════════════════════════════════════════════════
# results/
#   {hostname}_{YYYYMMDD}_{HHMMSS}/    ← one folder per target
#     apex_report.html                 ← visual dashboard (open in browser)
#     apex_report.json                 ← machine-readable full findings
#     apex_report.md                   ← markdown report
#     findings.csv                     ← spreadsheet (Excel/Google Sheets)
#     poc_scripts.sh                   ← ready-to-run curl PoC commands
#     burp_requests.txt                ← Burp Suite request templates
#     ai_analysis.md                   ← Claude claude-opus-4-8 attack chains + remediation
#   ai_executive_report_{ts}.md        ← board-level risk summary (all targets)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE REFERENCE
# ══════════════════════════════════════════════════════════════════════════════
# Phase  1  Passive OSINT — DNS, TLS, CT logs, Wayback
# Phase  2  WAF + tech fingerprinting
# Phase  3  Security headers, CSP, CORS, cookies
# Phase  4  JavaScript, sourcemaps, secret scanning
# Phase  5  API mapping, GraphQL, path probing, S3
# Phase  6  Subdomain takeover, SSRF, IDOR, XSS
# Phase  7  Advanced: smuggling, JWT, OAuth, HPP, SSTI, XXE, proto-pollution
# Phase  8  SQLi, NoSQLi, CMDi, file upload, CSRF, JSONP, LFI, 2FA bypass
# Phase  9  GQL batch, CRLF, SAML, race conditions, cloud SSRF, mass assignment
# Phase 10  Log4Shell, XPath/LDAP inject, PDF-SSRF, JWT alg confusion, blind XXE
# Phase 11  JWT kid, ZIP slip, SAML XSW, PKCE downgrade, H2C smuggling, ImageMagick
# Phase 12  RCE OOB, shell upload, NTLM leak, cloud IMDS, K8s/Docker API, Redis
# Phase 13  OGNL/SpEL/SSTI, OAuth2 device, AzureAD, Nginx/Traefik misconfig, mXSS
# Phase 14  HTTP smuggling FE, cache deception, race condition, GraphQL deep, JWT brute
# Phase 15  OAuth2 hijack, HTTP desync TE, CORS chain, OpenAPI fuzz, crypto weakness
# Phase 16  Auth harvest → multi-stage chain → WAF-bypass upload → post-RCE map → adaptive bypass
