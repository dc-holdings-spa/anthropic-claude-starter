#!/usr/bin/env node
// PreToolUse hook: bloquea lecturas de .env / credentials / secrets
// Exit 2 → bloquea + stderr feedback a Claude

process.stdin.setEncoding("utf8");
let input = "";
process.stdin.on("data", (d) => (input += d));
process.stdin.on("end", () => {
    let args;
    try { args = JSON.parse(input); } catch { process.exit(0); }

    const toolInput = args.tool_input || {};
    const target = toolInput.file_path || toolInput.path || toolInput.pattern || "";
    const targetLower = target.toLowerCase();

    const BLOCKED_PATTERNS = [
        ".env",
        "credentials.json",
        "credentials.yml",
        "secrets.yml",
        "secrets.yaml",
        "id_rsa",
        "id_ed25519",
        ".pem",
    ];

    for (const pat of BLOCKED_PATTERNS) {
        if (targetLower.includes(pat)) {
            console.error(`Cannot read sensitive file matching '${pat}': ${target}`);
            console.error("Use environment variables or secret manager instead.");
            process.exit(2);
        }
    }

    process.exit(0);
});
