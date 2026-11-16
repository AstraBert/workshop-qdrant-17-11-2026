const EXAMPLES = [
  "CRISPR off-target effects",
  "gut microbiome and depression",
  "how do tumors resist immunotherapy?",
];

const form = document.querySelector("#search-form");
const queryInput = document.querySelector("#query");
const statusLine = document.querySelector("#status");
const resultsList = document.querySelector("#results");

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function selectedMode() {
  return document.querySelector("input[name=mode]:checked").value;
}

function numberOrNull(selector) {
  const value = document.querySelector(selector).value;
  return value === "" ? null : Number(value);
}

function readFilters() {
  return {
    title_contains: document.querySelector("#title-contains").value.trim(),
    abstract_excludes: document.querySelector("#abstract-excludes").value.trim(),
    pmid_min: numberOrNull("#pmid-min"),
    pmid_max: numberOrNull("#pmid-max"),
  };
}

function renderHit(hit) {
  const title = element("h2");
  const link = element("a", "", hit.title);
  link.href = `https://pubmed.ncbi.nlm.nih.gov/${hit.pmid}/`;
  link.target = "_blank";
  link.rel = "noopener";
  title.append(link);

  const meta = element("div", "meta");
  meta.append(element("span", "", `PMID ${hit.pmid}`));
  meta.append(element("span", "", `score ${hit.score.toFixed(3)}`));

  const abstract = element("p", "abstract", hit.content);
  abstract.addEventListener("click", () => abstract.classList.toggle("expanded"));

  const item = element("li", "result");
  item.append(title, meta, abstract);
  return item;
}

function renderResults({ hits, search_ms }) {
  resultsList.replaceChildren(...hits.map(renderHit));
  statusLine.className = "status";
  statusLine.textContent =
    `${hits.length} results · ${Math.round(search_ms)} ms, embedding included`;
}

function renderError(message) {
  resultsList.replaceChildren();
  statusLine.className = "status error";
  statusLine.textContent = message;
}

async function search(query) {
  statusLine.className = "status";
  statusLine.textContent = "Searching…";
  const response = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      mode: selectedMode(),
      filters: readFilters(),
      limit: 10,
    }),
  });
  if (!response.ok) {
    renderError(`Search failed (${response.status}).`);
    return;
  }
  renderResults(await response.json());
}

function runSearch(query) {
  queryInput.value = query;
  search(query).catch(() => renderError("Could not reach the server."));
}

async function showInfo() {
  const response = await fetch("/api/info");
  const { documents } = await response.json();
  document.querySelector("#info").textContent =
    `Qdrant Cloud · ${documents.toLocaleString("en-US")} abstracts`;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runSearch(queryInput.value.trim());
});

// Changing the mode repeats the current search.
for (const radio of document.querySelectorAll("input[name=mode]")) {
  radio.addEventListener("change", () => {
    if (queryInput.value.trim()) runSearch(queryInput.value.trim());
  });
}

for (const example of EXAMPLES) {
  const chip = element("button", "chip", example);
  chip.type = "button";
  chip.addEventListener("click", () => runSearch(example));
  document.querySelector("#examples").append(chip);
}

// A link such as /?q=crispr runs that search on page load.
const initialQuery = new URLSearchParams(location.search).get("q");
if (initialQuery) runSearch(initialQuery);

showInfo();
