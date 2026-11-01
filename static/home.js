const $ = (id) => document.getElementById(id);
const SVG = "http://www.w3.org/2000/svg";
let report = null;
let selected = "current";
let selectedDate = null;

function node(tag, attributes = {}, text) {
  const element = document.createElementNS(SVG, tag);
  for (const [name, value] of Object.entries(attributes))
    element.setAttribute(name, value);
  if (text !== undefined) element.textContent = text;
  return element;
}

function choose(name) {
  if (!report) return;
  selected = name;
  $("previewCurrent").setAttribute("aria-pressed", String(name === "current"));
  $("previewAlternative").setAttribute(
    "aria-pressed",
    String(name === "alternative"),
  );
  const portfolio = report.portfolios[name];
  const totalReturn = portfolio.metrics.total_return * 100;
  const drawdown = portfolio.metrics.max_drawdown * 100;
  $("previewReturn").replaceChildren(
    document.createTextNode(totalReturn.toFixed(2)),
    Object.assign(document.createElement("span"), { textContent: "%" }),
  );
  $("previewDrawdown").textContent = drawdown.toFixed(2) + "%";
  $("previewCaption").textContent = portfolio.allocations
    .map((row) => `${row.symbol} ${row.weight_percent.toFixed(0)}%`)
    .join(" · ");
  $("previewLineName").textContent =
    name === "current" ? "Current allocation" : "Alternative allocation";
  renderChart();
}

function inspect(index) {
  if (!report) return;
  selectedDate = Math.max(0, Math.min(report.dates.length - 1, index));
  $("homeInspect").value = selectedDate;
  const portfolio = report.portfolios[selected].index[selectedDate];
  const benchmark = report.portfolios.benchmark.index[selectedDate];
  $("homeReadout").textContent =
    `${report.dates[selectedDate]} · Allocation ${portfolio.toFixed(2)} · ETF ${benchmark.toFixed(2)}`;
  $("homeInspect").setAttribute("aria-valuetext", $("homeReadout").textContent);
  const svg = $("homeChart").querySelector("svg");
  if (!svg) return;
  const width = Number(svg.dataset.width);
  const x = 37 + (selectedDate / (report.dates.length - 1)) * (width - 47);
  svg.querySelector("[data-cursor]").setAttribute("x1", x);
  svg.querySelector("[data-cursor]").setAttribute("x2", x);
}

function renderChart() {
  if (!report) return;
  const host = $("homeChart");
  const width = Math.max(245, Math.round(host.clientWidth));
  const height = Math.max(210, Math.round(host.clientHeight));
  const left = 37,
    right = width - 10,
    top = 14,
    bottom = height - 27;
  const all = [
    ...report.portfolios[selected].index,
    ...report.portfolios.benchmark.index,
  ];
  let low = Math.floor(Math.min(...all) / 10) * 10;
  let high = Math.ceil(Math.max(...all) / 10) * 10;
  if (high === low) high += 10;
  const x = (i) => left + (i / (report.dates.length - 1)) * (right - left);
  const y = (value) => bottom - ((value - low) / (high - low)) * (bottom - top);
  const svg = node("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label":
      "Actual saved historical allocation and NIFTY ETF indices; both start at 100",
    "data-width": width,
  });
  for (let i = 0; i < 4; i++) {
    const value = low + (i / 3) * (high - low);
    svg.append(
      node("line", {
        x1: left,
        x2: right,
        y1: y(value),
        y2: y(value),
        stroke: "#e9ede3",
        "stroke-width": 1,
      }),
    );
    svg.append(
      node(
        "text",
        {
          x: left - 8,
          y: y(value) + 3,
          "text-anchor": "end",
          fill: "#87927f",
          "font-size": 9,
        },
        value.toFixed(0),
      ),
    );
  }
  for (const [name, colour] of [
    ["benchmark", "#83918b"],
    [selected, "#3157ff"],
  ]) {
    const path = report.portfolios[name].index
      .map(
        (value, i) =>
          `${i ? "L" : "M"}${x(i).toFixed(2)},${y(value).toFixed(2)}`,
      )
      .join(" ");
    svg.append(
      node("path", {
        d: path,
        fill: "none",
        stroke: colour,
        "stroke-width": name === "benchmark" ? 1.5 : 2,
        "stroke-linejoin": "round",
        "stroke-linecap": "round",
      }),
    );
    const finalValue = report.portfolios[name].index.at(-1);
    svg.append(
      node("circle", {
        cx: right,
        cy: y(finalValue),
        r: name === "benchmark" ? 2.5 : 3,
        fill: colour,
      }),
    );
  }
  svg.append(
    node(
      "text",
      { x: left, y: height - 7, fill: "#87927f", "font-size": 9 },
      report.dates[0].slice(0, 4),
    ),
  );
  svg.append(
    node(
      "text",
      {
        x: right,
        y: height - 7,
        fill: "#87927f",
        "font-size": 9,
        "text-anchor": "end",
      },
      report.dates.at(-1).slice(0, 4),
    ),
  );
  svg.append(
    node("line", {
      x1: right,
      x2: right,
      y1: top,
      y2: bottom,
      stroke: "#c6cfbd",
      "stroke-width": 1,
      "stroke-dasharray": "3 4",
      "data-cursor": "",
    }),
  );
  const pointer = (event) => {
    const point =
      ((event.clientX - svg.getBoundingClientRect().left) /
        svg.getBoundingClientRect().width) *
      width;
    inspect(
      Math.round(((point - left) / (right - left)) * (report.dates.length - 1)),
    );
  };
  svg.addEventListener("pointermove", pointer);
  svg.addEventListener("pointerdown", pointer);
  host.replaceChildren(svg);
  inspect(selectedDate ?? report.dates.length - 1);
}

$("previewCurrent").addEventListener("click", () => choose("current"));
$("previewAlternative").addEventListener("click", () => choose("alternative"));
$("homeInspect").addEventListener("input", (event) =>
  inspect(Number(event.target.value)),
);

async function loadPreview() {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch("/home-preview", {
      signal: controller.signal,
    });
    if (!response.ok) throw new Error("Saved preview is unavailable");
    const data = await response.json();
    if (
      !Array.isArray(data.dates) ||
      data.dates.length < 2 ||
      !data.dates.every(
        (date) => typeof date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(date),
      ) ||
      !["current", "alternative", "benchmark"].every((name) => {
        const portfolio = data.portfolios?.[name];
        return (
          Array.isArray(portfolio?.index) &&
          portfolio.index.length === data.dates.length &&
          portfolio.index.every(
            (value) => Number.isFinite(value) && value > 0,
          ) &&
          Number.isFinite(portfolio.metrics?.total_return) &&
          Number.isFinite(portfolio.metrics?.max_drawdown) &&
          Array.isArray(portfolio.allocations) &&
          portfolio.allocations.length > 0 &&
          portfolio.allocations.every(
            (row) =>
              typeof row.symbol === "string" &&
              Number.isFinite(row.weight_percent),
          )
        );
      })
    )
      throw new Error("Invalid saved preview");
    report = data;
    $("previewCurrent").disabled = false;
    $("previewAlternative").disabled = false;
    $("homeInspect").disabled = false;
    $("homeInspect").max = report.dates.length - 1;
    $("previewDataset").textContent =
      `SAVED DATA · ${report.dates[0].slice(0, 4)}–${report.dates.at(-1).slice(0, 4)}`;
    $("previewCoverage").textContent =
      `${report.dates[0]} – ${report.dates.at(-1)} · ${report.dates.length} matching observations · adjusted prices · buy and hold`;
    choose(selected);
  } catch {
    report = null;
    $("previewReturn").textContent = "—";
    $("previewDrawdown").textContent = "—";
    $("previewCurrent").disabled = true;
    $("previewAlternative").disabled = true;
    $("homeInspect").disabled = true;
    $("previewDataset").textContent = "SAVED EXAMPLE · UNAVAILABLE";
    $("homeChart").replaceChildren(
      Object.assign(document.createElement("p"), {
        className: "chart-loading",
        textContent:
          "The local saved dataset is unavailable. Open the workspace for setup details or to retrieve historical data.",
      }),
    );
    $("homeReadout").textContent =
      "No calculated results are shown without the saved dataset.";
    $("previewCoverage").textContent = "Saved historical coverage unavailable.";
  } finally {
    window.clearTimeout(timeout);
    $("homePreview").setAttribute("aria-busy", "false");
  }
}

let previousWidth = 0;
new ResizeObserver((entries) => {
  const width = entries[0].contentRect.width;
  if (width > 0 && width !== previousWidth) {
    previousWidth = width;
    renderChart();
  }
}).observe($("homeChart"));

if (
  !window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
  "IntersectionObserver" in window
) {
  const sections = document.querySelectorAll(
    ".preview-heading, .approach-grid article, .method-head, .closing-section > *",
  );
  document.documentElement.classList.add("reveal-ready");
  const reveal = new IntersectionObserver(
    (entries) =>
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          reveal.unobserve(entry.target);
        }
      }),
    { threshold: 0.08 },
  );
  sections.forEach((element) => {
    element.dataset.reveal = "";
    reveal.observe(element);
  });
}
loadPreview();
