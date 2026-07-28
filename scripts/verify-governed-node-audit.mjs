import { spawnSync } from "node:child_process";

const productionOnly = process.argv.includes("--prod");
const args = ["audit", "--json", ...(productionOnly ? ["--prod"] : [])];
const pnpmEntrypoint = process.env.npm_execpath;
const command = pnpmEntrypoint ? process.execPath : "pnpm";
const commandArgs = pnpmEntrypoint ? [pnpmEntrypoint, ...args] : args;
const result = spawnSync(command, commandArgs, {
  encoding: "utf8",
  maxBuffer: 10 * 1024 * 1024,
  shell: false,
});

if (result.error) {
  console.error(`Dependency audit could not execute: ${result.error.message}`);
  process.exit(2);
}

let report;
try {
  report = JSON.parse(result.stdout);
} catch {
  console.error("Dependency audit did not return valid JSON.");
  console.error(result.stderr);
  process.exit(2);
}

const advisories = Object.values(report.advisories ?? {});
if (advisories.length === 0 && result.status === 0) {
  console.log(`pnpm audit${productionOnly ? " --prod" : ""}: no known vulnerabilities.`);
  process.exit(0);
}

const governedPaths = new Set([
  "apps__web>eslint>minimatch>brace-expansion",
  "packages__eslint-config>eslint>minimatch>brace-expansion",
]);
const allowed = advisories.every(
  (advisory) =>
    advisory.github_advisory_id === "GHSA-mh99-v99m-4gvg" &&
    advisory.cves?.length === 1 &&
    advisory.cves[0] === "CVE-2026-14257" &&
    advisory.module_name === "brace-expansion" &&
    advisory.severity === "high" &&
    advisory.findings?.every((finding) => finding.paths?.every((path) => governedPaths.has(path))),
);
const exceptionExpiry = new Date("2026-10-28T00:00:00Z");

if (!allowed || advisories.length !== 1 || new Date() >= exceptionExpiry) {
  console.error(
    "Dependency audit contains an ungoverned advisory, a changed path/severity, or an expired exception.",
  );
  console.error(JSON.stringify(report, null, 2));
  process.exit(1);
}

console.warn(
  `Governed development-only advisory remains: GHSA-mh99-v99m-4gvg / CVE-2026-14257. ` +
    `Exception expires 2026-10-27; production remains prohibited.`,
);
