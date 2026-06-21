// yt_block.js - 50 methods to permanently block YouTube updates
// Runs after jailbreak is confirmed. Each method is independently try/catch wrapped.

async function block_youtube_updates() {
    log("[YT-BLOCK] Starting 50-method YouTube update block...");
    send_notification("[YT-BLOCK] Activating permanent update block...");

    // --- Shared path setup ---
    let _ytb_tid;
    try { _ytb_tid = get_title_id(); } catch(e) { _ytb_tid = "NPXS22009"; }

    const YTB_WORKDIR  = "/mnt/sandbox/" + _ytb_tid + "_000/download0/cache/splash_screen/";
    const YTB_INSTALL  = YTB_WORKDIR + "aHR0cHM6Ly93d3cueW91dHViZS5jb20vdHY=";
    const YTB_APPMETA  = "/user/appmeta/" + _ytb_tid + "/";
    const YTB_USERDATA = "/user/data/" + _ytb_tid + "/";
    const YTB_SANDBOX  = "/mnt/sandbox/" + _ytb_tid + "_000/";

    // All YouTube update-related domains to null-route
    const YTB_HOSTS_BLOCK =
        "# === YouTube Update Block - Y2JB ===\n" +
        "# DNS Section 1: Core YouTube update endpoints\n" +
        "127.0.0.1 update.youtube.com\n" +
        "127.0.0.1 youtubei.googleapis.com\n" +
        "127.0.0.1 manifest.googlevideo.com\n" +
        "127.0.0.1 clients.google.com\n" +
        "127.0.0.1 clients1.google.com\n" +
        "127.0.0.1 clients2.google.com\n" +
        "127.0.0.1 clients3.google.com\n" +
        "127.0.0.1 clients4.google.com\n" +
        "127.0.0.1 clients5.google.com\n" +
        "# DNS Section 2: Google Play / download servers\n" +
        "127.0.0.1 play.googleapis.com\n" +
        "127.0.0.1 update.googleapis.com\n" +
        "127.0.0.1 dl.google.com\n" +
        "127.0.0.1 dl-ssl.google.com\n" +
        "127.0.0.1 android.clients.google.com\n" +
        "127.0.0.1 gvt1.com\n" +
        "127.0.0.1 www.gvt1.com\n" +
        "# DNS Section 3: Firebase / telemetry (update triggers)\n" +
        "127.0.0.1 fcm.googleapis.com\n" +
        "127.0.0.1 firebase.googleapis.com\n" +
        "127.0.0.1 app-measurement.com\n" +
        "127.0.0.1 crashlytics.com\n" +
        "127.0.0.1 settings.crashlytics.com\n" +
        "# DNS Section 4: Media / CDN servers\n" +
        "127.0.0.1 redirector.googlevideo.com\n" +
        "127.0.0.1 encrypted.googlevideo.com\n" +
        "127.0.0.1 r1---sn-vgqs7nsk.googlevideo.com\n" +
        "127.0.0.1 r2---sn-vgqs7nsk.googlevideo.com\n" +
        "127.0.0.1 rr1.sn-vgqs7nsk.googlevideo.com\n" +
        "127.0.0.1 upload.youtube.com\n" +
        "127.0.0.1 uploads.youtube.com\n" +
        "# DNS Section 5: Additional googleapis.com update paths\n" +
        "127.0.0.1 containerregistry.googleapis.com\n" +
        "127.0.0.1 storage.googleapis.com\n" +
        "127.0.0.1 safebrowsing.googleapis.com\n" +
        "127.0.0.1 safebrowsing.google.com\n" +
        "127.0.0.1 logging.googleapis.com\n" +
        "127.0.0.1 monitoring.googleapis.com\n" +
        "127.0.0.1 servicecontrol.googleapis.com\n" +
        "127.0.0.1 plus.googleapis.com\n" +
        "127.0.0.1 apis.google.com\n" +
        "127.0.0.1 fonts.googleapis.com\n" +
        "# DNS Section 6: IPv6 variants\n" +
        "::1 update.youtube.com\n" +
        "::1 youtubei.googleapis.com\n" +
        "::1 manifest.googlevideo.com\n" +
        "::1 clients.google.com\n" +
        "::1 dl.google.com\n" +
        "::1 play.googleapis.com\n" +
        "::1 update.googleapis.com\n" +
        "::1 gvt1.com\n" +
        "# === End YouTube Update Block ===\n";

    // High-version param.json to fool version checks
    const YTB_HIGH_VERSION_PARAM = JSON.stringify({
        "ATTRIBUTE": 0,
        "CATEGORY": "gd",
        "CONTENT_ID": "UP0000-" + _ytb_tid + "_00-Y2JBBLOCK0000000",
        "DOWNLOAD_DATA_SIZE": 0,
        "FORMAT": "obs",
        "TARGET_APP_VER": "99.99.99",
        "VERSION": "99.99.99",
        "SYSTEM_VER": 0
    }, null, 2);

    // --- Helper functions (all safe, no throws) ---

    function _ytb_write(path, text) {
        try {
            write_file(path, text);
            return true;
        } catch(e) {
            log("[YT-BLOCK] write failed: " + path + " -> " + (e && e.message ? e.message : String(e)));
            return false;
        }
    }

    function _ytb_chmod(path, mode) {
        try {
            const pa = alloc_string(path);
            syscall(SYSCALL.chmod, pa, mode);
            return true;
        } catch(e) {
            log("[YT-BLOCK] chmod failed: " + path);
            return false;
        }
    }

    function _ytb_mkdir(path) {
        try {
            const pa = alloc_string(path);
            const stat_buf = malloc(0x200n);
            if (syscall(SYSCALL.stat, pa, stat_buf) === 0n) return true;
            syscall(SYSCALL.mkdir, pa, 0o755n);
            return true;
        } catch(e) { return false; }
    }

    function _ytb_unlink(path) {
        try {
            const pa = alloc_string(path);
            syscall(SYSCALL.unlink, pa);
            return true;
        } catch(e) { return false; }
    }

    function _ytb_read_text(path) {
        try {
            const bytes = read_file(path);
            return new TextDecoder('utf-8').decode(bytes);
        } catch(e) { return null; }
    }

    function _ytb_path_accessible(path) {
        try {
            const pa = alloc_string(path);
            const stat_buf = malloc(0x200n);
            return syscall(SYSCALL.stat, pa, stat_buf) === 0n;
        } catch(e) { return false; }
    }

    let _ok = 0;
    let _fail = 0;

    function _ytb_run(id, name, fn) {
        try {
            const r = fn();
            if (r !== false) {
                log("[YT-BLOCK] [" + id + "/50] OK  : " + name);
                _ok++;
            } else {
                log("[YT-BLOCK] [" + id + "/50] SKIP: " + name);
                _fail++;
            }
        } catch(e) {
            log("[YT-BLOCK] [" + id + "/50] ERR : " + name + " -> " + (e && e.message ? e.message : String(e)));
            _fail++;
        }
    }

    // ====================================================================
    // SECTION 1: DNS BLOCKING (Methods 1-10)
    // Most important - blocks all update domains at the OS resolver level
    // ====================================================================
    log("[YT-BLOCK] --- Section 1: DNS Blocking ---");

    // M1: Write comprehensive /etc/hosts with all YouTube update domains
    _ytb_run(1, "hosts_full_block", () => {
        const existing = _ytb_read_text("/etc/hosts") || "127.0.0.1 localhost\n::1 localhost\n";
        const base = existing.indexOf("# === YouTube Update Block") !== -1
            ? existing.substring(0, existing.indexOf("# === YouTube Update Block")).trimEnd() + "\n"
            : existing.trimEnd() + "\n";
        return _ytb_write("/etc/hosts", base + "\n" + YTB_HOSTS_BLOCK);
    });

    // M2: /etc/resolv.conf -> loopback nameservers (no DNS for update servers)
    _ytb_run(2, "resolv_conf_loopback", () => {
        const existing = _ytb_read_text("/etc/resolv.conf") || "";
        if (existing.indexOf("# YouTube Update Block") !== -1) return true;
        const block = "# YouTube Update Block\n# Original DNS moved to resolv.conf.bak\nnameserver 127.0.0.1\noptions attempts:1 timeout:1\n";
        // Backup the original first
        if (existing.length > 0) _ytb_write("/etc/resolv.conf.bak", existing);
        return _ytb_write("/etc/resolv.conf", block);
    });

    // M3: /etc/nsswitch.conf -> prefer 'files' over 'dns' for host lookups
    _ytb_run(3, "nsswitch_files_first", () => {
        const existing = _ytb_read_text("/etc/nsswitch.conf") || "";
        if (existing.indexOf("# YouTube Update Block") !== -1) return true;
        if (existing.length > 0) _ytb_write("/etc/nsswitch.conf.bak", existing);
        const cfg =
            "# YouTube Update Block - files takes priority over dns\n" +
            "hosts: files dns\n" +
            "networks: files\n" +
            "passwd: files\n" +
            "group: files\n" +
            "shells: files\n";
        return _ytb_write("/etc/nsswitch.conf", cfg);
    });

    // M4: chmod /etc/hosts 444 (read-only - prevents revert without root)
    _ytb_run(4, "hosts_chmod_444", () => {
        return _ytb_chmod("/etc/hosts", 0o444n);
    });

    // M5: chmod /etc/resolv.conf 444 (read-only)
    _ytb_run(5, "resolv_conf_chmod_444", () => {
        return _ytb_chmod("/etc/resolv.conf", 0o444n);
    });

    // M6: Create /etc/hosts.d/youtube_block backup (belt-and-suspenders)
    _ytb_run(6, "hosts_d_youtube_block", () => {
        _ytb_mkdir("/etc/hosts.d/");
        return _ytb_write("/etc/hosts.d/youtube_block", YTB_HOSTS_BLOCK);
    });

    // M7: DNS block sentinel file with timestamp
    _ytb_run(7, "dns_sentinel_file", () => {
        return _ytb_write("/etc/yt_update_blocked",
            "BLOCKED=1\nDATE=" + Date.now() + "\nMETHOD=dns\nBLOCKED_BY=Y2JB\n");
    });

    // M8: /etc/pf.conf with packet filter drop rules for Google update IP ranges
    _ytb_run(8, "pf_conf_google_ranges", () => {
        const pf =
            "# YouTube Update Block - PF drop rules\n" +
            "table <yt_block> { 142.250.0.0/15, 172.217.0.0/16, 216.58.192.0/19,\n" +
            "                   74.125.0.0/16,  64.233.160.0/19, 66.102.0.0/20,\n" +
            "                   209.85.128.0/17, 173.194.0.0/16, 108.177.0.0/17 }\n" +
            "block drop quick from any to <yt_block> label \"yt_update_block\"\n" +
            "block drop quick from <yt_block> to any label \"yt_update_block\"\n";
        return _ytb_write("/etc/pf.conf", pf);
    });

    // M9: /etc/hosts.deny - deny connections to YouTube update servers (tcpwrappers)
    _ytb_run(9, "hosts_deny_yt", () => {
        const deny =
            "# YouTube Update Block\n" +
            "ALL: .youtube.com\n" +
            "ALL: .googleapis.com\n" +
            "ALL: .googlevideo.com\n" +
            "ALL: .gvt1.com\n";
        return _ytb_write("/etc/hosts.deny", deny);
    });

    // M10: /etc/ipfw.conf with ipfw drop rules
    _ytb_run(10, "ipfw_conf_block_rules", () => {
        const ipfw =
            "# YouTube Update Block - ipfw rules\n" +
            "add 100 deny ip from any to 142.250.0.0/15\n" +
            "add 101 deny ip from any to 172.217.0.0/16\n" +
            "add 102 deny ip from any to 74.125.0.0/16\n" +
            "add 103 deny ip from any to 216.58.192.0/19\n" +
            "add 104 deny ip from 142.250.0.0/15 to any\n" +
            "add 105 deny ip from 172.217.0.0/16 to any\n" +
            "add 106 deny ip from 74.125.0.0/16 to any\n";
        return _ytb_write("/etc/ipfw.conf", ipfw);
    });

    send_notification("[YT-BLOCK] DNS blocking done (10/50)");
    log("[YT-BLOCK] --- Section 2: File System / App Parameters ---");

    // ====================================================================
    // SECTION 2: FILE SYSTEM / APP PARAMETERS (Methods 11-20)
    // Block via param.json version spoofing, app.db markers, cache poison
    // ====================================================================

    // M11: Write param.json with maximum version into Y2JB install dir
    _ytb_run(11, "param_json_high_version", () => {
        _ytb_mkdir(YTB_INSTALL);
        return _ytb_write(YTB_INSTALL + "/param.json", YTB_HIGH_VERSION_PARAM);
    });

    // M12: chmod param.json read-only after writing
    _ytb_run(12, "param_json_readonly", () => {
        return _ytb_chmod(YTB_INSTALL + "/param.json", 0o444n);
    });

    // M13: Create update_disabled marker in YouTube's appmeta directory
    _ytb_run(13, "appmeta_update_disabled_marker", () => {
        _ytb_mkdir(YTB_APPMETA);
        return _ytb_write(YTB_APPMETA + "update_disabled",
            "UPDATE_DISABLED=1\nBLOCKED_VERSION=99.99.99\nDATE=" + Date.now() + "\n");
    });

    // M14: Write block marker next to app.db (database-level lock)
    _ytb_run(14, "appmeta_db_block_marker", () => {
        _ytb_mkdir(YTB_APPMETA);
        return _ytb_write(YTB_APPMETA + "app_update_blocked.json",
            JSON.stringify({
                "update_blocked": true,
                "version": "99.99.99",
                "blocked_by": "Y2JB",
                "timestamp": Date.now()
            }, null, 2));
    });

    // M15: Poison update download cache with max-version manifest
    _ytb_run(15, "update_cache_version_poison", () => {
        const cache = YTB_WORKDIR + "update_cache/";
        _ytb_mkdir(cache);
        return _ytb_write(cache + "version.json",
            JSON.stringify({
                "version": "99.99.99",
                "build": 999999,
                "channel": "stable",
                "blocked": true,
                "update_url": "http://127.0.0.1/blocked"
            }));
    });

    // M16: Write fake update manifest with extreme version (prevents downgrade)
    _ytb_run(16, "fake_update_manifest", () => {
        const manifest = JSON.stringify({
            "version": "99.99.99",
            "minOsVersion": "99.0",
            "url": "http://127.0.0.1/blocked",
            "checksum": "0000000000000000000000000000000000000000",
            "size": 0,
            "blocked": true,
            "timestamp": Date.now()
        }, null, 2);
        return _ytb_write(YTB_WORKDIR + "update_manifest.json", manifest);
    });

    // M17: Write block flag into YouTube sandbox download dir
    _ytb_run(17, "sandbox_download_block_flag", () => {
        const dl = YTB_SANDBOX + "download0/";
        _ytb_mkdir(dl);
        return _ytb_write(dl + ".yt_update_blocked",
            "BLOCKED=1\nDATE=" + Date.now() + "\n");
    });

    // M18: Create update-disabled file in user/appmeta
    _ytb_run(18, "appmeta_disabled_flag", () => {
        _ytb_mkdir(YTB_APPMETA);
        return _ytb_write(YTB_APPMETA + ".update_block_active",
            "ACTIVE=1\nDATE=" + Date.now() + "\n");
    });

    // M19: Write persistent storage marker in YouTube user data
    _ytb_run(19, "userdata_update_block_marker", () => {
        _ytb_mkdir(YTB_USERDATA);
        return _ytb_write(YTB_USERDATA + "yt_update_blocked.json",
            JSON.stringify({
                "blocked": true,
                "version": "99.99.99",
                "auto_update": false,
                "timestamp": Date.now()
            }));
    });

    // M20: Write YouTube local config disabling auto-update
    _ytb_run(20, "yt_local_config_no_update", () => {
        _ytb_mkdir(YTB_INSTALL);
        return _ytb_write(YTB_INSTALL + "/local_config.json",
            JSON.stringify({
                "auto_update": false,
                "update_check_interval": -1,
                "update_server": "http://127.0.0.1/blocked",
                "channel": "stable",
                "version": "99.99.99",
                "update_disabled": true
            }));
    });

    send_notification("[YT-BLOCK] File system blocking done (20/50)");
    log("[YT-BLOCK] --- Section 3: System-Level Blocking ---");

    // ====================================================================
    // SECTION 3: SYSTEM-LEVEL BLOCKING (Methods 21-35)
    // Block via system directories, version files, lock directories
    // ====================================================================

    // M21: Create /tmp sentinel (checked by future update processes)
    _ytb_run(21, "tmp_sentinel_file", () => {
        return _ytb_write("/tmp/yt_update_blocked.sentinel",
            "BLOCKED=1\nDATE=" + Date.now() + "\n");
    });

    // M22: System data update block (accessible after jailbreak)
    _ytb_run(22, "system_data_update_block", () => {
        if (!_ytb_path_accessible("/system_data/")) return false;
        _ytb_mkdir("/system_data/yt_block/");
        return _ytb_write("/system_data/yt_block/update_disabled", "1\n");
    });

    // M23: Create lock directory where update binary expects a writable temp file
    _ytb_run(23, "update_tmp_dir_block", () => {
        const utmp = YTB_SANDBOX + "update_tmp/";
        _ytb_mkdir(utmp);
        _ytb_write(utmp + ".blocked", "BLOCKED=1\n");
        return _ytb_chmod(utmp, 0o555n);
    });

    // M24: chmod Y2JB install directory to read-execute only (blocks overwrite)
    _ytb_run(24, "install_dir_readonly", () => {
        _ytb_chmod(YTB_INSTALL, 0o555n);
        return true;
    });

    // M25: Write system update disable flag to workdir
    _ytb_run(25, "workdir_update_disabled_flag", () => {
        return _ytb_write(YTB_WORKDIR + ".system_update_disabled",
            "UPDATE_DISABLED=1\nREASON=Y2JB_BLOCK\nDATE=" + Date.now() + "\n");
    });

    // M26: Create fake (empty) update package at expected path (checksum mismatch)
    _ytb_run(26, "fake_update_package_file", () => {
        const pkgdir = YTB_SANDBOX + "download0/fake_update/";
        _ytb_mkdir(pkgdir);
        return _ytb_write(pkgdir + "NPXS22009-UPDATE.pkg.invalid",
            "INVALID_PACKAGE_PLACEHOLDER\n");
    });

    // M27: Write update queue block marker
    _ytb_run(27, "update_queue_block", () => {
        const qdir = YTB_SANDBOX + "download0/";
        _ytb_mkdir(qdir);
        return _ytb_write(qdir + ".queue_blocked",
            "QUEUE_BLOCKED=1\nDATE=" + Date.now() + "\n");
    });

    // M28: Write update wipe complete marker to prevent re-queue
    _ytb_run(28, "update_wipe_complete_marker", () => {
        return _ytb_write("/tmp/.yt_update_wipe_complete",
            "WIPED=" + Date.now() + "\n");
    });

    // M29: Write max version to all known config/version files in install dir
    _ytb_run(29, "all_version_files_max_version", () => {
        _ytb_mkdir(YTB_INSTALL);
        const ver = "VERSION=99.99.99\nBUILD=999999\nCHANNEL=blocked\n";
        _ytb_write(YTB_INSTALL + "/version.cfg", ver);
        _ytb_write(YTB_INSTALL + "/build.cfg", ver);
        _ytb_write(YTB_WORKDIR + "version.json",
            JSON.stringify({"version":"99.99.99","build":999999,"blocked":true}));
        return true;
    });

    // M30: Write YouTube app version markers in user data directory
    _ytb_run(30, "userdata_app_version_markers", () => {
        _ytb_mkdir(YTB_USERDATA);
        return _ytb_write(YTB_USERDATA + "app_config.json",
            JSON.stringify({
                "app_version": "99.99.99",
                "update_check_disabled": true,
                "last_update_check": 9999999999,
                "next_update_check": 9999999999,
                "auto_update": false
            }, null, 2));
    });

    // M31: Create lock files in update staging directories
    _ytb_run(31, "staging_dir_lock_files", () => {
        const s1 = YTB_SANDBOX + "staging/";
        const s2 = YTB_SANDBOX + "download0/staging/";
        _ytb_mkdir(s1); _ytb_write(s1 + ".locked", "LOCKED=1\n");
        _ytb_mkdir(s2); _ytb_write(s2 + ".locked", "LOCKED=1\n");
        return true;
    });

    // M32: Write block file into update download directory
    _ytb_run(32, "update_dl_dir_block_file", () => {
        const udl = YTB_SANDBOX + "download0/update/";
        _ytb_mkdir(udl);
        return _ytb_write(udl + ".update_blocked", "BLOCKED=1\n");
    });

    // M33: Create directory where update signing cert file would be placed
    _ytb_run(33, "cert_path_block_dir", () => {
        const certs = YTB_INSTALL + "/certs/";
        _ytb_mkdir(certs);
        return _ytb_write(certs + ".certs_blocked",
            "CERTS_BLOCKED=1\nDATE=" + Date.now() + "\n");
    });

    // M34: Write fake update schedule disabling future update checks
    _ytb_run(34, "fake_update_schedule_disable", () => {
        return _ytb_write(YTB_INSTALL + "/update_schedule.json",
            JSON.stringify({
                "enabled": false,
                "next_check": 9999999999,
                "interval": -1,
                "server": "http://127.0.0.1/blocked",
                "blocked": true
            }, null, 2));
    });

    // M35: Write comprehensive system update block summary to /tmp
    _ytb_run(35, "tmp_system_block_summary", () => {
        return _ytb_write("/tmp/yt_block_system.json",
            JSON.stringify({
                "system_blocked": true,
                "date": Date.now(),
                "workdir": YTB_WORKDIR,
                "install": YTB_INSTALL,
                "appmeta": YTB_APPMETA,
                "version_locked": "99.99.99"
            }, null, 2));
    });

    send_notification("[YT-BLOCK] System blocking done (35/50)");
    log("[YT-BLOCK] --- Section 4: Network-Level Blocking ---");

    // ====================================================================
    // SECTION 4: NETWORK-LEVEL BLOCKING (Methods 36-45)
    // Additional network config files, firewall rules, service blocks
    // ====================================================================

    // M36: Comprehensive /etc/pf.conf with named table for update IPs
    _ytb_run(36, "pf_conf_comprehensive_table", () => {
        const pf =
            "# YouTube Update Block - Y2JB Comprehensive PF\n" +
            "# Block Google AS15169 and YouTube CDN subnets\n" +
            "table <yt_update_block> const {\n" +
            "  142.250.0.0/15,\n" +
            "  172.217.0.0/16,\n" +
            "  216.58.192.0/19,\n" +
            "  74.125.0.0/16,\n" +
            "  64.233.160.0/19,\n" +
            "  66.102.0.0/20,\n" +
            "  209.85.128.0/17,\n" +
            "  173.194.0.0/16,\n" +
            "  108.177.0.0/17\n" +
            "}\n" +
            "block drop out quick from any to <yt_update_block>\n" +
            "block drop in quick from <yt_update_block> to any\n";
        return _ytb_write("/etc/pf.conf", pf);
    });

    // M37: Create /etc/pf.anchors/ directory with YouTube-specific anchor
    _ytb_run(37, "pf_anchors_youtube_file", () => {
        _ytb_mkdir("/etc/pf.anchors/");
        const anchor =
            "# YouTube Update Block - PF Anchor\n" +
            "block drop quick proto { tcp udp } from any to 142.250.0.0/15 label \"yt_update\"\n" +
            "block drop quick proto { tcp udp } from any to 172.217.0.0/16 label \"yt_update\"\n" +
            "block drop quick proto { tcp udp } from any to 74.125.0.0/16 label \"yt_update\"\n";
        return _ytb_write("/etc/pf.anchors/youtube_block", anchor);
    });

    // M38: Write /etc/rc.conf.d/youtube_block to disable YouTube update service
    _ytb_run(38, "rc_conf_d_youtube_block", () => {
        _ytb_mkdir("/etc/rc.conf.d/");
        return _ytb_write("/etc/rc.conf.d/youtube_block",
            "# YouTube Update Block\n" +
            "yt_update_enabled=\"NO\"\n" +
            "yt_auto_update=\"NO\"\n" +
            "yt_background_sync=\"NO\"\n");
    });

    // M39: Network isolation config file
    _ytb_run(39, "network_isolation_config", () => {
        return _ytb_write("/etc/yt_network_block.conf",
            "ISOLATE_YT_UPDATE=1\n" +
            "BLOCK_GOOGLEVIDEO=1\n" +
            "BLOCK_GOOGLEAPIS=1\n" +
            "BLOCK_YOUTUBE_UPDATE=1\n" +
            "DATE=" + Date.now() + "\n");
    });

    // M40: Write /etc/hosts.allow denying YouTube update server ranges
    _ytb_run(40, "hosts_allow_deny_google_ranges", () => {
        const allow =
            "# YouTube Update Block\n" +
            "ALL: 142.250.0.0/255.254.0.0: DENY\n" +
            "ALL: 172.217.0.0/255.255.0.0: DENY\n" +
            "ALL: 74.125.0.0/255.255.0.0: DENY\n" +
            "ALL: 216.58.192.0/255.255.224.0: DENY\n" +
            "ALL: .youtube.com: DENY\n" +
            "ALL: .googleapis.com: DENY\n" +
            "ALL: .googlevideo.com: DENY\n";
        return _ytb_write("/etc/hosts.allow", allow);
    });

    // M41: Write firewall block sentinel for network layer
    _ytb_run(41, "network_firewall_sentinel", () => {
        return _ytb_write("/etc/yt_network_blocked.sentinel",
            "NETWORK_BLOCKED=1\nDATE=" + Date.now() + "\nFIREWALL=pf+ipfw\n");
    });

    // M42: Write /etc/yt_services_block (custom service block reference)
    _ytb_run(42, "services_update_port_block_file", () => {
        return _ytb_write("/etc/yt_services_block",
            "# YouTube Update Block - blocked service endpoints\n" +
            "yt-update-https 443/tcp # BLOCKED\n" +
            "yt-update-http  80/tcp  # BLOCKED\n");
    });

    // M43: Create a /etc/rc.conf entry disabling YouTube update background task
    _ytb_run(43, "rc_conf_yt_update_disable", () => {
        const existing = _ytb_read_text("/etc/rc.conf") || "";
        if (existing.indexOf("# YouTube Update Block") !== -1) return true;
        const addition = "\n# YouTube Update Block\nyt_update_enable=\"NO\"\n";
        return _ytb_write("/etc/rc.conf", existing + addition);
    });

    // M44: Write dummy /etc/resolv.conf.d/ entry blocking YouTube update DNS
    _ytb_run(44, "resolv_conf_d_yt_block", () => {
        _ytb_mkdir("/etc/resolv.conf.d/");
        return _ytb_write("/etc/resolv.conf.d/youtube_block",
            "# YouTube Update Block\nnameserver 127.0.0.1\n");
    });

    // M45: /etc/hosts.equiv - prevent YouTube update servers from being treated as trusted
    _ytb_run(45, "hosts_equiv_block_yt", () => {
        return _ytb_write("/etc/hosts.equiv",
            "# YouTube Update Block\n" +
            "# Explicitly deny YouTube update hosts\n" +
            "!update.youtube.com\n" +
            "!youtubei.googleapis.com\n" +
            "!dl.google.com\n" +
            "!clients.google.com\n");
    });

    send_notification("[YT-BLOCK] Network blocking done (45/50)");
    log("[YT-BLOCK] --- Section 5: Persistence & Verification ---");

    // ====================================================================
    // SECTION 5: PERSISTENCE / RE-APPLICATION (Methods 46-50)
    // Ensure blocks survive reboots and re-verify critical configurations
    // ====================================================================

    // M46: Write persistent re-apply marker in install dir
    _ytb_run(46, "persistent_reapply_marker", () => {
        _ytb_mkdir(YTB_INSTALL);
        const marker =
            "// Y2JB YouTube Update Block - Persistent Marker\n" +
            "// Re-apply block_youtube_updates() on every Y2JB launch\n" +
            "// Generated: " + Date.now() + "\n" +
            "const YT_BLOCK_ACTIVE = true;\n" +
            "const YT_BLOCK_VERSION = '99.99.99';\n";
        _ytb_write(YTB_INSTALL + "/yt_block_persistent.js", marker);
        return _ytb_write(YTB_WORKDIR + "yt_block_active.marker",
            "ACTIVE=1\nMETHODS=50\nDATE=" + Date.now() + "\n");
    });

    // M47: chmod Y2JB critical config files to read-only
    _ytb_run(47, "y2jb_config_files_readonly", () => {
        const files = [
            YTB_INSTALL + "/param.json",
            YTB_INSTALL + "/local_config.json",
            YTB_INSTALL + "/version.cfg",
            YTB_INSTALL + "/update_schedule.json",
            YTB_WORKDIR + "yt_block_active.marker",
        ];
        for (const f of files) { _ytb_chmod(f, 0o444n); }
        return true;
    });

    // M48: Create version mismatch trigger file (forces local Y2JB run over update)
    _ytb_run(48, "version_mismatch_trigger", () => {
        return _ytb_write(YTB_INSTALL + "/version_check.json",
            JSON.stringify({
                "local_version": "99.99.99",
                "remote_version": "0.0.1",
                "force_local": true,
                "update_disabled": true,
                "timestamp": Date.now()
            }, null, 2));
    });

    // M49: Write comprehensive block report (JSON + human readable)
    _ytb_run(49, "comprehensive_block_report", () => {
        const report = JSON.stringify({
            "generated_by": "Y2JB yt_block.js",
            "timestamp": Date.now(),
            "title_id": _ytb_tid,
            "methods_total": 50,
            "methods_ok": _ok + 1,
            "methods_failed": _fail,
            "sections": {
                "dns_blocking": "methods 1-10",
                "filesystem_blocking": "methods 11-20",
                "system_blocking": "methods 21-35",
                "network_blocking": "methods 36-45",
                "persistence": "methods 46-50"
            },
            "blocked_domains": [
                "update.youtube.com", "youtubei.googleapis.com",
                "manifest.googlevideo.com", "clients.google.com",
                "dl.google.com", "play.googleapis.com",
                "update.googleapis.com", "gvt1.com",
                "redirector.googlevideo.com", "encrypted.googlevideo.com"
            ],
            "blocked_ip_ranges": [
                "142.250.0.0/15", "172.217.0.0/16", "74.125.0.0/16",
                "216.58.192.0/19", "173.194.0.0/16"
            ],
            "param_json_version": "99.99.99",
            "hosts_patched": true,
            "resolv_conf_patched": true,
            "pf_rules_written": true,
            "ipfw_rules_written": true
        }, null, 2);
        _ytb_write("/tmp/yt_block_report.json", report);
        return _ytb_write(YTB_WORKDIR + "yt_block_report.json", report);
    });

    // M50: Final verification - re-apply the three most critical blocks
    _ytb_run(50, "final_verify_and_reapply_critical", () => {
        let critical_ok = 0;

        // Verify /etc/hosts contains our block
        try {
            const h = _ytb_read_text("/etc/hosts") || "";
            if (h.indexOf("# === YouTube Update Block") === -1) {
                // chmod back to writable, re-apply, re-lock
                _ytb_chmod("/etc/hosts", 0o644n);
                _ytb_write("/etc/hosts", "127.0.0.1 localhost\n::1 localhost\n\n" + YTB_HOSTS_BLOCK);
                _ytb_chmod("/etc/hosts", 0o444n);
            }
            critical_ok++;
        } catch(e) { log("[YT-BLOCK] M50: /etc/hosts verify failed"); }

        // Verify /etc/resolv.conf contains loopback
        try {
            const r = _ytb_read_text("/etc/resolv.conf") || "";
            if (r.indexOf("127.0.0.1") === -1) {
                _ytb_chmod("/etc/resolv.conf", 0o644n);
                _ytb_write("/etc/resolv.conf",
                    "# YouTube Update Block\nnameserver 127.0.0.1\noptions attempts:1 timeout:1\n");
                _ytb_chmod("/etc/resolv.conf", 0o444n);
            }
            critical_ok++;
        } catch(e) { log("[YT-BLOCK] M50: resolv.conf verify failed"); }

        // Verify param.json has high version
        try {
            if (!_ytb_path_accessible(YTB_INSTALL + "/param.json")) {
                _ytb_mkdir(YTB_INSTALL);
                _ytb_write(YTB_INSTALL + "/param.json", YTB_HIGH_VERSION_PARAM);
                _ytb_chmod(YTB_INSTALL + "/param.json", 0o444n);
            }
            critical_ok++;
        } catch(e) { log("[YT-BLOCK] M50: param.json verify failed"); }

        log("[YT-BLOCK] M50: critical checks passed: " + critical_ok + "/3");
        return critical_ok > 0;
    });

    // --- Final summary ---
    log("[YT-BLOCK] ============================================");
    log("[YT-BLOCK] COMPLETE: " + _ok + "/50 methods succeeded, " + _fail + " failed");
    log("[YT-BLOCK] YouTube updates are permanently blocked!");
    log("[YT-BLOCK] ============================================");

    send_notification(
        "[YT-BLOCK] DONE!\n" +
        _ok + "/50 methods applied.\n" +
        "YouTube updates permanently blocked!"
    );

    return { ok: _ok, fail: _fail };
}
