#!/usr/bin/env bash
# APEX_HUNTER v1.0 — PoC Verification
# Run from authorized device with Saudi IP


# [{f.severity}] {f.id}: {f.title} | {host}
# CWE: CWE-693 | CVSS: 5.4
curl -sI 'https://help.flynas.com'


# [{f.severity}] {f.id}: {f.title} | {host}
# CWE: CWE-1021 | CVSS: 5.4
curl -sI 'https://help.flynas.com' | grep -i 'x-frame\|frame-ancestors'


# [{f.severity}] {f.id}: {f.title} | {host}
# CWE: CWE-918 | CVSS: 0.0
curl -sk 'https://help.flynas.com?link=http%3A//link.help.flynas.com.YOUR_OOB_DOMAIN.burpcollaborator.net/'


# [{f.severity}] {f.id}: {f.title} | {host}
# CWE: CWE-200 | CVSS: 0.0
curl -sk 'https://help.flynas.com/.well-known/security.txt'
