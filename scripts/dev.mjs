import { existsSync } from "node:fs";
import path from "node:path";
import { spawn, execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const frontendDir = path.join(rootDir, "frontend");
const backendDir = path.join(rootDir, "backend");

const isProd = process.argv.includes("--prod");
const backendHost = process.env.BACKEND_HOST || "127.0.0.1";
const backendPort = process.env.BACKEND_PORT || "8000";
const frontendPort = process.env.PORT || process.env.FRONTEND_PORT || "3000";
const backendInternalUrl = `http://${backendHost}:${backendPort}`;

function resolvePythonExecutable() {
  const candidates =
    process.platform === "win32"
      ? [
          path.join(rootDir, ".venv", "Scripts", "python.exe"),
          path.join(backendDir, ".venv", "Scripts", "python.exe"),
          "python",
        ]
      : [
          path.join(rootDir, ".venv", "bin", "python"),
          path.join(backendDir, ".venv", "bin", "python"),
          "python3",
          "python",
        ];

  for (const candidate of candidates) {
    if (!candidate.includes(path.sep) || existsSync(candidate)) {
      return candidate;
    }
  }
  return "python";
}

function prefixStream(stream, label, target) {
  let buffer = "";
  stream.on("data", (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.length > 0) {
        target.write(`[${label}] ${line}\n`);
      }
    }
  });
  stream.on("end", () => {
    if (buffer.length > 0) {
      target.write(`[${label}] ${buffer}\n`);
    }
  });
}

function killProcessTree(child) {
  if (!child || !child.pid || child.killed) return;
  try {
    if (process.platform === "win32") {
      execFileSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
        stdio: "ignore",
      });
    } else {
      child.kill("SIGTERM");
    }
  } catch {
    // Process already exited
  }
}

async function waitForBackendHealth(url, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (shuttingDown) return false;
    try {
      const res = await fetch(`${url}/api/health`, {
        signal: AbortSignal.timeout(1500),
      });
      if (res.ok) return true;
    } catch {
      // Backend still starting
    }
    await new Promise((r) => setTimeout(r, 350));
  }
  return false;
}

let backendProc = null;
let frontendProc = null;
let shuttingDown = false;

function shutdown(exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  killProcessTree(frontendProc);
  killProcessTree(backendProc);
  process.exit(exitCode);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

async function main() {
  const pythonExec = resolvePythonExecutable();
  const nextBin = path.join(frontendDir, "node_modules", "next", "dist", "bin", "next");

  if (!existsSync(nextBin)) {
    console.error(
      "[webscout] Frontend dependencies not found. Run `npm --prefix frontend install` first."
    );
    process.exit(1);
  }

  console.log(
    `[webscout] Starting WebScout (${isProd ? "production" : "development"})...`
  );
  console.log(
    `[webscout] Internal API -> ${backendInternalUrl} | App URL -> http://localhost:${frontendPort}`
  );

  backendProc = spawn(
    pythonExec,
    [
      "-m",
      "uvicorn",
      "app.main:app",
      "--app-dir",
      backendDir,
      "--host",
      backendHost,
      "--port",
      backendPort,
    ],
    {
      cwd: rootDir,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  prefixStream(backendProc.stdout, "backend", process.stdout);
  prefixStream(backendProc.stderr, "backend", process.stderr);

  backendProc.on("exit", (code) => {
    if (!shuttingDown) {
      console.error(`[webscout] Backend exited unexpectedly (code ${code ?? 1}).`);
      shutdown(code ?? 1);
    }
  });

  const healthy = await waitForBackendHealth(backendInternalUrl, 15000);
  if (shuttingDown) return;
  if (!healthy) {
    console.warn(
      "[webscout] Backend health check did not finish within 15s; starting frontend anyway."
    );
  }

  const nextArgs = [nextBin, isProd ? "start" : "dev", "-p", frontendPort, "-H", "localhost"];
  frontendProc = spawn(process.execPath, nextArgs, {
    cwd: frontendDir,
    env: {
      ...process.env,
      NEXT_PUBLIC_API_URL: "",
      BACKEND_INTERNAL_URL: backendInternalUrl,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  prefixStream(frontendProc.stdout, "frontend", process.stdout);
  prefixStream(frontendProc.stderr, "frontend", process.stderr);

  frontendProc.on("exit", (code) => {
    if (!shuttingDown) {
      console.error(`[webscout] Frontend exited (code ${code ?? 0}).`);
      shutdown(code ?? 0);
    }
  });
}

main().catch((err) => {
  console.error("[webscout] Startup failure:", err);
  shutdown(1);
});
