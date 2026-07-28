import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const originalHead = document.head.innerHTML;

beforeEach(() => {
  vi.resetModules();
});

afterEach(() => {
  document.head.innerHTML = originalHead;
});

// What tiled.server.app renders into index.html for a given root path.
const serverRendered = (rootPath: string) =>
  `<base href="${rootPath}/ui/" />` +
  `<script type="application/json" id="tiled-runtime-config">` +
  `${JSON.stringify({
    root_path: rootPath,
    api_url: `${rootPath}/api/v1`,
  })}</script>`;

async function loadSettings(head: string) {
  document.head.innerHTML = head;
  const { rootPath, uiBasePath, defaultApiUrl } = await import("./settings");
  return { rootPath, uiBasePath, defaultApiUrl };
}

describe("runtime UI base", () => {
  it.each([
    ["", "/ui"],
    ["/tenant/tiled", "/tenant/tiled/ui"],
    ["/tenant/ui/tiled", "/tenant/ui/tiled/ui"],
  ])("uses root %s for UI base %s", async (rootPath, uiBasePath) => {
    expect(await loadSettings(serverRendered(rootPath))).toEqual({
      rootPath,
      uiBasePath,
      defaultApiUrl: `${rootPath}/api/v1`,
    });
  });

  it("falls back to Vite's development base", async () => {
    expect(await loadSettings("")).toEqual({
      rootPath: "",
      uiBasePath: "/ui",
      defaultApiUrl: "/api/v1",
    });
  });
});
