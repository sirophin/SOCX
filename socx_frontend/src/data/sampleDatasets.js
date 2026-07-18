/**
 * Static catalog for the Sample Datasets feature.
 *
 * There is no backend endpoint for this yet (by design — see the page
 * component). Every file listed here is real and lives in
 * /public/sample-datasets/, so the Download button works today with no
 * backend at all:
 *   - The Windows sample is a real Windows Security event log (not
 *     synthetic) — the same fixture used to build and test the backend's
 *     EVTX parser, verified to parse 100% cleanly.
 *   - All other samples are synthetic but format-valid — the Linux,
 *     Apache, and Nginx ones were verified by running them through the
 *     actual backend parsers (100% parsed, 0 failures) before being
 *     added here, so they're genuinely realistic and immediately usable
 *     as upload test data. Firewall/IDS/VPN don't have a backend parser
 *     yet, so those are illustrative only.
 *
 * `expectedAlerts` is a curated training figure — "how many distinct
 * suspicious indicators this dataset was designed to contain" — not a
 * live count from the Detection Engine (there's no default rule set
 * pre-seeded, so it can't be computed automatically yet).
 */

export const CATEGORIES = ['Windows', 'Linux', 'Apache', 'Nginx', 'Firewall', 'IDS', 'VPN']

export const SAMPLE_DATASETS = [
  {
    id: 'windows-privilege-use',
    category: 'Windows',
    name: 'Windows Security — Privilege Use & Account Management',
    description:
      'Real captured Windows Security event log. Mostly legitimate logon and privilege-use activity (4624, 4672, 4648) — the training exercise is spotting the 2 new local account creations (4720) buried in that noise.',
    difficulty: 'Advanced',
    expectedAlerts: 2,
    fileSize: '2.1 MB',
    fileName: 'windows_security_privilege_use.evtx',
    format: 'EVTX',
  },
  {
    id: 'linux-ssh-bruteforce',
    category: 'Linux',
    name: 'Linux auth.log — SSH Brute Force Campaign',
    description:
      '222 failed SSH login attempts against invalid/common usernames from a small pool of source IPs, followed by one successful login. Classic threshold-based brute-force pattern.',
    difficulty: 'Beginner',
    expectedAlerts: 1,
    fileSize: '24.5 KB',
    fileName: 'linux_auth_ssh_bruteforce.log',
    format: 'auth.log',
  },
  {
    id: 'linux-new-user-sudo-abuse',
    category: 'Linux',
    name: 'Linux auth.log — New User & Sudo Abuse',
    description:
      'A new service account is created, then used to read /etc/shadow, weaken /etc/passwd permissions, and fetch-and-execute a remote payload via sudo.',
    difficulty: 'Intermediate',
    expectedAlerts: 4,
    fileSize: '709 B',
    fileName: 'linux_auth_new_user_sudo_abuse.log',
    format: 'auth.log',
  },
  {
    id: 'apache-sql-injection',
    category: 'Apache',
    name: 'Apache Access Log — SQL Injection Attempts',
    description:
      'sqlmap-driven SQL injection attempts (UNION-based and boolean-based) against a product/search endpoint, 4 distinct payload variants across 80 requests.',
    difficulty: 'Beginner',
    expectedAlerts: 4,
    fileSize: '9.3 KB',
    fileName: 'apache_sql_injection.log',
    format: 'Combined Log Format',
  },
  {
    id: 'apache-directory-traversal',
    category: 'Apache',
    name: 'Apache Access Log — Directory Traversal & Enumeration',
    description:
      'Path traversal and sensitive-file enumeration attempts — /etc/passwd, .git/config, .env, wp-admin setup — across 60 requests from 2 source IPs.',
    difficulty: 'Beginner',
    expectedAlerts: 5,
    fileSize: '6.2 KB',
    fileName: 'apache_directory_traversal.log',
    format: 'Combined Log Format',
  },
  {
    id: 'nginx-credential-stuffing',
    category: 'Nginx',
    name: 'Nginx Access Log — Credential Stuffing',
    description:
      'Automated POST requests to /login from 40 distinct source IPs (python-requests user-agent), overwhelmingly 401s — a single credential-stuffing campaign spread thin to dodge simple per-IP rate limits.',
    difficulty: 'Intermediate',
    expectedAlerts: 1,
    fileSize: '15.2 KB',
    fileName: 'nginx_credential_stuffing.log',
    format: 'Combined Log Format',
  },
  {
    id: 'nginx-xss-probing',
    category: 'Nginx',
    name: 'Nginx Access Log — XSS Probing',
    description:
      'Reflected XSS probing across search, comment, and profile endpoints — 3 distinct payload styles (script tag, encoded script tag, img/onerror).',
    difficulty: 'Beginner',
    expectedAlerts: 3,
    fileSize: '5.9 KB',
    fileName: 'nginx_xss_probing.log',
    format: 'Combined Log Format',
  },
  {
    id: 'firewall-port-scan',
    category: 'Firewall',
    name: 'Firewall Log — Sequential Port Scan',
    description:
      'One source IP sweeping 300 sequential destination ports on an internal host in under 5 minutes, all denied by the default rule — textbook port scan.',
    difficulty: 'Beginner',
    expectedAlerts: 1,
    fileSize: '28.1 KB',
    fileName: 'firewall_port_scan.log',
    format: 'Firewall (syslog-style)',
  },
  {
    id: 'firewall-c2-beacon',
    category: 'Firewall',
    name: 'Firewall Log — Outbound C2 Beacon Pattern',
    description:
      'An internal host making allowed outbound HTTPS connections to the same external IP every 15 minutes for 15 hours straight — near-identical byte counts each time. Easy to miss among normal outbound traffic; the regularity is the tell.',
    difficulty: 'Advanced',
    expectedAlerts: 1,
    fileSize: '8.2 KB',
    fileName: 'firewall_c2_beacon.log',
    format: 'Firewall (syslog-style)',
  },
  {
    id: 'ids-malware-c2',
    category: 'IDS',
    name: 'IDS Alerts — Malware C2 Communication',
    description:
      'Suricata/Snort-style alerts spanning 3 signature classes (Cobalt Strike check-in, generic trojan callback, suspicious DNS to known C2 domain) over roughly 2.5 hours.',
    difficulty: 'Intermediate',
    expectedAlerts: 3,
    fileSize: '9.4 KB',
    fileName: 'ids_malware_c2.log',
    format: 'Suricata/Snort fast.log',
  },
  {
    id: 'ids-exploit-attempts',
    category: 'IDS',
    name: 'IDS Alerts — Exploit Attempt Signatures',
    description:
      'Alerts for 3 well-known exploit signatures: Log4Shell (CVE-2021-44228), SQL injection in URI, and an EternalBlue (MS17-010) probe.',
    difficulty: 'Intermediate',
    expectedAlerts: 3,
    fileSize: '8.1 KB',
    fileName: 'ids_exploit_attempts.log',
    format: 'Suricata/Snort fast.log',
  },
  {
    id: 'vpn-unusual-login-times',
    category: 'VPN',
    name: 'VPN Log — Unusual Login Times & Geolocation',
    description:
      '3 users connecting in a tight rotation from 4 different countries in under an hour — each user individually shows an implausible travel pattern.',
    difficulty: 'Advanced',
    expectedAlerts: 3,
    fileSize: '2.5 KB',
    fileName: 'vpn_unusual_login_times.log',
    format: 'OpenVPN (syslog-style)',
  },
  {
    id: 'vpn-concurrent-session',
    category: 'VPN',
    name: 'VPN Log — Concurrent Session Anomaly',
    description:
      'The same user account establishing overlapping sessions from 20 different source IPs in under 15 minutes — a strong sign of shared/compromised credentials.',
    difficulty: 'Advanced',
    expectedAlerts: 1,
    fileSize: '1.7 KB',
    fileName: 'vpn_concurrent_session_anomaly.log',
    format: 'OpenVPN (syslog-style)',
  },
]
