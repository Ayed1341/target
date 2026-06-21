/*
 * YouTube Update Blocker — standalone patch
 * Blocks YouTube app update checks on PS5
 * by ayed oraybi
 */

async function block_youtube_updates() {
    try {
        await ulog("yt-block: Starting YouTube update protection...");

        // Block YouTube update URLs via DNS-style blocking
        const yt_block_hosts = [
            "*.youtube.com",
            "*.youtubei.com",
            "*.ytimg.com",
            "*.googlevideo.com",
        ];

        // Write hosts block
        const hosts_content = 
            "# YouTube update block by ayed oraybi\n" +
            "127.0.0.1 update.googleapis.com\n" +
            "127.0.0.1 android.clients.google.com\n" +
            "0.0.0.0 www.youtube.com/api/feeds/videos\n";

        const hosts_paths = [
            "/data/hosts_block.txt",
            "/user/temp/hosts_block.txt",
        ];

        for (const hp of hosts_paths) {
            try {
                write_file(hp, hosts_content);
                await ulog("yt-block: Written hosts block to " + hp);
            } catch (_) {}
        }

        // Disable YouTube auto-update via param.json patch
        try {
            const param_paths = [
                "/user/app/NPXS20001/sce_sys/param.json",
                "/system/app/NPXS20001/sce_sys/param.json",
            ];

            for (const pp of param_paths) {
                try {
                    let param_data = read_file(pp);
                    // Disable update check
                    param_data = param_data.replace(
                        /"enableUpdateCheck":\s*true/g,
                        '"enableUpdateCheck": false'
                    );
                    write_file(pp, param_data);
                    await ulog("yt-block: Patched " + pp);
                } catch (_) {}
            }
        } catch (_) {}

        await ulog("yt-block: YouTube update protection ACTIVE");
        return true;
    } catch (e) {
        await ulog("yt-block: Error: " + e.message);
        return false;
    }
}
