import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const originalHead = document.head.innerHTML;

beforeEach(() => {
  vi.resetModules();
});

afterEach(() => {
  document.head.innerHTML = originalHead;
});

async function loadSettings(head: string) {
  document.head.innerHTML = head;
  const { rootPath, uiBasePath, bootstrapApiUrl } = await import("./settings");
  return { rootPath, uiBasePath, bootstrapApiUrl };
}

describe("runtime UI base", () => {
  it.each([
    ["", "/ui"],
    ["/tenant/tiled", "/tenant/tiled/ui"],
    ["/tenant/ui/tiled", "/tenant/ui/tiled/ui"],
  ])("uses root %s for UI base %s", async (rootPath, uiBasePath) => {
    expect(await loadSettings(`<base href="${rootPath}/ui/" />`)).toEqual({
      rootPath,
      uiBasePath,
      bootstrapApiUrl: `${rootPath}/api/v1`,
    });
  });

  it("falls back to the default base when no <base> is served", async () => {
    expect(await loadSettings("")).toEqual({
      rootPath: "",
      uiBasePath: "/ui",
      bootstrapApiUrl: "/api/v1",
    });
  });
});
