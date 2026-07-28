// The server rewrites index.html's <base> to the prefix it serves under,
// e.g. "/tenant/tiled/ui/".
const DEFAULT_UI_BASE_PATH = "/ui";

const uiBasePath = document.querySelector("base")
  ? new URL(document.baseURI).pathname.replace(/\/$/, "")
  : DEFAULT_UI_BASE_PATH;
const rootPath = uiBasePath.replace(/\/ui$/, "");
const bootstrapApiUrl = `${rootPath}/api/v1`;

const tiledUISettingsURL = `${rootPath}/tiled-ui-settings`;

interface Column {
  header: string;
  field: string;
  select_metadata: string;
}

interface Spec {
  spec: string;
  columns: Column[];
  default_columns: string[];
}

interface SpecView {
  spec: string;
  url: string;
}

interface Settings {
  api_url: string;
  specs: Spec[];
  spec_views?: SpecView[];
  structure_families: any;
}

const fetchSettings = async (signal: AbortSignal): Promise<Settings> => {
  const response = await fetch(tiledUISettingsURL, { signal });
  return (await response.json()) as Settings;
};

export { fetchSettings, bootstrapApiUrl, rootPath, uiBasePath };
export type { Settings };
