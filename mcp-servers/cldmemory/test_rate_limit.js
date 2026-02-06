const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

test("rate limit plugin is registered", () => {
  const content = fs.readFileSync(path.join(__dirname, "index.js"), "utf8");
  assert.match(content, /@fastify\/rate-limit/);
  assert.match(content, /fastify\.register\(rateLimit/);
});
