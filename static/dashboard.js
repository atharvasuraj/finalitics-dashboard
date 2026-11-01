import {
  canonicalSymbol,
  mergeAllocation,
  allocationHint,
  requestCoordinator,
} from "./dashboard_state.js";

let invalidateController = () => {};
function controllerFailure(error) {
  console.error(
    "The dashboard controller could not complete the analysis.",
    error,
  );
  invalidateController();
  const byId = (id) => document.getElementById(id);
  if (byId("error")) {
    byId("error").textContent =
      "The dashboard could not display this analysis. Reload the page and try again. If this follows an update, restart the local server first.";
    byId("error").hidden = false;
  }
  if (byId("results")) byId("results").hidden = true;
  if (byId("buildStage")) byId("buildStage").hidden = false;
  if (byId("exploreStage")) byId("exploreStage").hidden = true;
  if (byId("stale")) byId("stale").hidden = true;
  if (byId("status")) byId("status").textContent = "Analysis was not accepted.";
  if (byId("commentary")) byId("commentary").replaceChildren();
  for (const id of ["interpret", "printReport", "navExplore", "navNotes"])
    if (byId(id)) byId(id).disabled = true;
  document.body.dataset.reportReady = "false";
}

window.addEventListener("error", (event) => controllerFailure(event.error));
window.addEventListener("unhandledrejection", (event) =>
  controllerFailure(event.reason),
);

function initializeDashboard() {
  const $ = (id) => document.getElementById(id);
  const names = {
    current: "Current",
    alternative: "Alternative",
    benchmark: "NIFTY ETF",
  };
  const colors = {
    current: "#3157ff",
    alternative: "#b66c2e",
    benchmark: "#83918b",
  };
  const requests = requestCoordinator();
  const cursorUpdaters = new Map();
  let report = null,
    rows = [],
    stale = true,
    selectedIndex = 0;
  invalidateController = () => {
    requests.invalidate();
    report = null;
    stale = true;
    cursorUpdaters.clear();
    // An old template may be missing a control. The fallback error still needs
    // to be visible even if normal control synchronization cannot run.
    try {
      sync();
    } catch {
      // The outer failure boundary owns the message.
    }
  };
  const pct = (value) => (100 * value).toFixed(2) + "%";
  const entries = () =>
    ["current", "alternative", "benchmark"]
      .filter((name) => report.portfolios[name])
      .map((name) => [name, report.portfolios[name]]);

  function sync() {
    const alternative = $("useAlternative").checked;
    const { totals, problems } = allocationHint(rows, alternative);
    $("totals").textContent =
      `Current: ${totals.current.toFixed(2)}%` +
      (alternative ? ` · Alternative: ${totals.alternative.toFixed(2)}%` : "");
    $("allocationHint").textContent =
      problems.join(" ") ||
      "Allocation totals are ready. Server validation also applies.";
    $("calculate").disabled =
      problems.length > 0 ||
      requests.busy("calculation") ||
      requests.busy("import");
    const calculating = String(requests.busy("calculation"));
    $("calculate").setAttribute("aria-busy", calculating);
    $("buildStage").setAttribute("aria-busy", calculating);
    $("interpret").disabled = !report || stale || requests.busy("commentary");
    $("csv").disabled = requests.busy("import");
    $("add").disabled = rows.length >= 10;
    $("stockLimit").textContent =
      rows.length >= 10
        ? "Ten-stock limit reached. Remove a row to add another stock."
        : `${rows.length}/10 stocks`;
    const saved = $("source").value === "saved";
    $("start").disabled = $("end").disabled = saved;
    $("sourceHint").textContent = saved
      ? "Fixed 2022–2024 data: RELIANCE.NS, HDFCBANK.NS and INFY.NS. Choose Retrieve history for other stocks or dates."
      : "NSE/INR only; dates are inclusive. At least 252 shared observations are required.";
    document.querySelectorAll("[data-alternative]").forEach((input) => {
      input.disabled = !alternative;
    });
    for (const id of ["csvTarget", "allocationView"]) {
      const option = $(id).querySelector('option[value="alternative"]');
      option.disabled =
        id === "csvTarget" ? !alternative : !report?.portfolios.alternative;
      option.hidden = option.disabled;
      if (option.disabled && $(id).value === "alternative")
        $(id).value = "current";
    }
    $("printReport").disabled = !report || stale;
    document.body.dataset.reportReady = String(!!report && !stale);
    $("quickStart").disabled = requests.busy("calculation");
    $("navExplore").disabled = $("navNotes").disabled = !report;
    $("altHeading").hidden = !alternative;
    document
      .querySelectorAll("[data-alt-column]")
      .forEach((cell) => (cell.hidden = !alternative));
    $("dataBadge").textContent = saved
      ? "Saved data · 2022–2024"
      : "Custom history · NSE / INR";
    mixPreview(totals.current);
  }

  function dirty() {
    requests.invalidate();
    stale = true;
    $("stale").hidden = !report;
    $("commentary").replaceChildren();
    $("aiStatus").textContent = report
      ? "Inputs changed; calculate again before requesting commentary."
      : "Not requested.";
    $("status").textContent = "";
    sync();
  }

  function reset() {
    rows = [
      { symbol: "RELIANCE.NS", current: 40, alternative: 20 },
      { symbol: "HDFCBANK.NS", current: 30, alternative: 40 },
      { symbol: "INFY.NS", current: 30, alternative: 40 },
    ];
    $("source").value = "saved";
    $("start").value = "2022-01-01";
    $("end").value = "2024-12-31";
    $("useAlternative").checked = true;
    edit();
    dirty();
  }

  function edit() {
    $("editor").replaceChildren();
    rows.forEach((row, i) => {
      const tr = document.createElement("tr");
      for (const key of ["symbol", "current", "alternative"]) {
        const td = document.createElement("td"),
          input = document.createElement("input");
        input.value = row[key];
        input.type = key === "symbol" ? "text" : "number";
        input.setAttribute("aria-label", `${key} row ${i + 1}`);
        if (key !== "symbol") {
          input.min = 0;
          input.max = 100;
          input.step = 0.01;
        }
        if (key === "alternative") {
          input.dataset.alternative = "";
          td.dataset.altColumn = "";
        }
        input.addEventListener("input", () => {
          rows[i][key] = input.value;
          dirty();
        });
        td.append(input);
        tr.append(td);
      }
      const td = document.createElement("td"),
        button = document.createElement("button");
      button.textContent = "×";
      button.setAttribute("aria-label", `Remove row ${i + 1}`);
      button.onclick = () => {
        rows.splice(i, 1);
        edit();
        dirty();
      };
      td.append(button);
      tr.append(td);
      $("editor").append(tr);
    });
  }

  async function post(url, payload, signal) {
    const response = await fetch(url, {
      method: "POST",
      signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Request failed.");
    return data;
  }

  function payload() {
    return {
      source: $("source").value,
      start: $("start").value,
      end: $("end").value,
      current: rows.map((r) => ({ symbol: r.symbol, weight: r.current })),
      alternative: $("useAlternative").checked
        ? rows.map((r) => ({ symbol: r.symbol, weight: r.alternative }))
        : null,
    };
  }
  function showError(error) {
    $("error").textContent = error.message;
    $("error").hidden = false;
  }
  $("calculate").onclick = () => {
    if (requests.busy("calculation") || $("calculate").disabled) return;
    dirty();
    const submitted = payload();
    requests.run(
      "calculation",
      (signal) => post("/dashboard/analyse", submitted, signal),
      {
        started: () => {
          sync();
          $("status").textContent = "Loading and aligning historical data…";
          $("error").hidden = true;
        },
        success: (value) => {
          try {
            report = value;
            stale = true;
            render();
            showWorkspace("explore", "overview");
            stale = false;
            requests.setAnalysis(value.analysis_id);
            $("status").textContent = "Calculated from matching dates.";
            $("exploreTitle").focus({ preventScroll: true });
          } catch (error) {
            controllerFailure(error);
          }
        },
        error: (error) => {
          showError(error);
          $("status").textContent =
            "Calculation failed. Correct the input or retry.";
        },
        settled: sync,
      },
    );
  };
  $("reset").onclick = reset;
  $("add").onclick = () => {
    if (rows.length < 10) {
      rows.push({ symbol: "", current: 0, alternative: 0 });
      edit();
      dirty();
    }
  };
  for (const id of ["source", "start", "end", "useAlternative"])
    $(id).addEventListener("change", () => {
      if ($("source").value === "saved") {
        $("start").value = "2022-01-01";
        $("end").value = "2024-12-31";
      }
      dirty();
    });
  $("csv").onchange = () => {
    const file = $("csv").files[0];
    if (!file || requests.busy("import")) return;
    if (file.size > 1024 * 1024) {
      showError(new Error("CSV exceeds 1 MB."));
      return;
    }
    const target = $("csvTarget").value,
      form = new FormData();
    form.append("file", file);
    dirty();
    requests.run(
      "import",
      async (signal) => {
        const response = await fetch("/dashboard/csv", {
          method: "POST",
          body: form,
          signal,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Import failed.");
        return mergeAllocation(rows, data.rows, target);
      },
      {
        started: sync,
        success: (value) => {
          rows = value;
          edit();
          $("status").textContent =
            `CSV replaced ${target} weights; the other allocation was preserved. Stocks absent from the CSV received zero ${target} weight.`;
          $("error").hidden = true;
        },
        error: showError,
        settled: () => {
          $("csv").value = "";
          sync();
        },
      },
    );
  };
  function svgElement(tag, attrs = {}) {
    const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    return e;
  }
  function inspect(i) {
    if (!report) return;
    selectedIndex = Math.max(
      0,
      Math.min(report.dates.length - 1, Math.round(i)),
    );
    $("inspection").textContent =
      report.dates[selectedIndex] +
      " · " +
      entries()
        .map(
          ([n, p]) =>
            `${names[n]}: ${p.index[selectedIndex].toFixed(2)} (drawdown ${p.drawdown[selectedIndex].toFixed(2)}%)`,
        )
        .join(" · ");
    $("riskInspection").textContent = $("inspection").textContent;
    for (const id of ["inspect", "riskInspect"]) {
      $(id).value = selectedIndex;
      $(id).setAttribute("aria-valuetext", $("inspection").textContent);
    }
    for (const update of cursorUpdaters.values()) update(selectedIndex);
  }
  function chart(id, key) {
    const host = $(id);
    cursorUpdaters.delete(id);
    host.replaceChildren();
    const width = Math.max(300, Math.round(host.clientWidth));
    const plotWidth = width - 75;
    const svg = svgElement("svg", {
      viewBox: `0 0 ${width} 280`,
      role: "img",
      "aria-label":
        key === "index"
          ? "Portfolio versus benchmark performance"
          : "Portfolio drawdown",
    });
    let all = Object.values(report.portfolios).flatMap((p) => p[key]),
      low = Math.min(...all),
      high = Math.max(...all);
    if (high === low) {
      high += 1;
      low -= 1;
    }
    const X = (i) => 55 + (i / (report.dates.length - 1)) * plotWidth,
      Y = (v) => 235 - ((v - low) / (high - low)) * 210;
    for (let i = 0; i < 5; i++) {
      let v = low + ((high - low) * i) / 4,
        y = Y(v);
      svg.append(
        svgElement("line", {
          x1: 55,
          x2: width - 20,
          y1: y,
          y2: y,
          stroke: "#e7ede9",
        }),
      );
      const t = svgElement("text", {
        x: 48,
        y: y + 4,
        "text-anchor": "end",
        fill: "#6c8074",
        "font-size": 11,
      });
      t.textContent = v.toFixed(1) + (key === "drawdown" ? "%" : "");
      svg.append(t);
    }
    for (const [name, p] of entries()) {
      const path = svgElement("path", {
        class: "series-line",
        d: p[key]
          .map(
            (v, i) => (i ? "L" : "M") + X(i).toFixed(1) + "," + Y(v).toFixed(1),
          )
          .join(" "),
        fill: "none",
        stroke: colors[name],
        "stroke-width": name === "current" ? 3 : 2,
        "stroke-dasharray": name === "benchmark" ? "5 5" : "none",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
      });
      const title = svgElement("title");
      title.textContent = names[name];
      path.append(title);
      svg.append(path);
    }
    for (const [i, anchor] of [
      [0, "start"],
      [report.dates.length - 1, "end"],
    ]) {
      const t = svgElement("text", {
        x: X(i),
        y: 266,
        "text-anchor": anchor,
        fill: "#6c8074",
        "font-size": 11,
      });
      t.textContent = report.dates[i];
      svg.append(t);
    }
    const cursor = svgElement("line", {
      x1: X(selectedIndex),
      x2: X(selectedIndex),
      y1: 20,
      y2: 235,
      stroke: "#a1b6aa",
      "stroke-dasharray": "3 3",
      "data-cursor": "",
    });
    cursorUpdaters.set(id, (i) => {
      cursor.setAttribute("x1", X(i));
      cursor.setAttribute("x2", X(i));
    });
    svg.append(cursor);
    const onPointer = (e) => {
      const x =
        ((e.clientX - svg.getBoundingClientRect().left) /
          svg.getBoundingClientRect().width) *
        width;
      const i = Math.max(
        0,
        Math.min(
          report.dates.length - 1,
          Math.round(((x - 55) / plotWidth) * (report.dates.length - 1)),
        ),
      );
      inspect(i);
    };
    svg.addEventListener("pointermove", onPointer);
    svg.addEventListener("pointerdown", onPointer);
    host.append(svg);
  }
  function allocationChart() {
    const key = $("allocationView").value,
      p = report.portfolios[key] || report.portfolios.current;
    const host = $("allocationChart");
    host.replaceChildren();
    for (const r of p.allocations) {
      const line = document.createElement("div");
      line.className = "bar";
      line.title = `${r.symbol}: ${r.weight_percent.toFixed(2)}% at inception`;
      const label = document.createElement("span");
      label.textContent = r.symbol;
      const bar = document.createElement("i");
      bar.style.width = `${r.weight_percent * 0.65}%`;
      const val = document.createElement("b");
      val.textContent = r.weight_percent.toFixed(2) + "%";
      line.append(label, bar, val);
      host.append(line);
    }
  }
  function render() {
    selectedIndex = report.dates.length - 1;
    cursorUpdaters.clear();
    $("empty").hidden = true;
    $("results").hidden = false;
    $("stale").hidden = true;
    $("interpret").disabled = false;
    $("commentary").replaceChildren();
    $("aiStatus").textContent = "Not requested.";
    $("period").textContent =
      `${report.period.start} → ${report.period.end} · ${report.period.observations} matched dates`;
    const metrics = $("metrics");
    metrics.replaceChildren();
    for (const [key, label] of [
      ["total_return", "Total return"],
      ["cagr", "CAGR"],
      ["annualized_volatility", "Annualized volatility"],
      ["max_drawdown", "Maximum drawdown"],
    ]) {
      const c = document.createElement("div");
      c.className = "metric";
      const l = document.createElement("span");
      l.textContent = label;
      const v = document.createElement("strong");
      v.textContent = pct(report.portfolios.current.metrics[key]);
      const help = document.createElement("small");
      help.textContent = {
        total_return: "Change over the actual period.",
        cagr: "Equivalent compound annual growth.",
        annualized_volatility: "Annualized variability of observed returns.",
        max_drawdown: "Largest observed fall from a prior peak.",
      }[key];
      c.append(l, v, help);
      metrics.append(c);
    }
    for (const id of ["legend", "riskLegend"]) {
      $(id).replaceChildren();
      for (const [k] of entries()) {
        const l = document.createElement("span");
        l.className = "legend";
        const dot = document.createElement("i");
        dot.style.background =
          k === "benchmark"
            ? `repeating-linear-gradient(90deg, ${colors[k]} 0 5px, transparent 5px 8px)`
            : colors[k];
        l.append(dot, document.createTextNode(names[k]));
        $(id).append(l);
      }
    }
    chart("performance", "index");
    chart("drawdown", "drawdown");
    $("inspect").max = $("riskInspect").max = report.dates.length - 1;
    inspect(selectedIndex);
    allocationChart();
    $("scenarioCards").replaceChildren();
    for (const [name, portfolio] of entries()) {
      const card = document.createElement("article");
      card.className = "scenario-card";
      const heading = document.createElement("h3");
      const dot = document.createElement("i");
      dot.style.background = colors[name];
      heading.append(dot, document.createTextNode(names[name]));
      const label = document.createElement("span");
      label.textContent = "TOTAL RETURN";
      const total = document.createElement("strong");
      total.textContent = pct(portfolio.metrics.total_return);
      card.append(heading, label, total);
      for (const [key, text] of [
        ["annualized_volatility", "Annualized volatility"],
        ["max_drawdown", "Maximum drawdown"],
      ]) {
        const detail = document.createElement("p");
        const value = document.createElement("b");
        value.textContent = pct(portfolio.metrics[key]);
        detail.append(document.createTextNode(text), value);
        card.append(detail);
      }
      $("scenarioCards").append(card);
    }
    const table = $("comparison");
    table.replaceChildren();
    let header = true;
    for (const cells of [
      ["Allocation", "Return", "CAGR", "Volatility", "Max drawdown"],
      ...entries().map(([n, p]) => [
        names[n],
        ...[
          "total_return",
          "cagr",
          "annualized_volatility",
          "max_drawdown",
        ].map((k) => pct(p.metrics[k])),
      ]),
    ]) {
      const tr = document.createElement("tr");
      for (const text of cells) {
        const td = document.createElement(header ? "th" : "td");
        if (header) td.scope = "col";
        td.textContent = text;
        tr.append(td);
      }
      if (!header)
        tr.firstChild.style.color =
          colors[entries()[table.rows.length - 1]?.[0]];
      table.append(tr);
      header = false;
    }
    const allocationTable = $("reportAllocations");
    allocationTable.replaceChildren();
    const allocationNames = entries().filter(([name]) => name !== "benchmark");
    const stocks = [
      ...new Set(
        allocationNames.flatMap(([, p]) =>
          p.allocations.map((row) => row.symbol),
        ),
      ),
    ];
    for (const [i, cells] of [
      ["Stock", ...allocationNames.map(([name]) => names[name] + " %")],
      ...stocks.map((symbol) => [
        symbol,
        ...allocationNames.map(([, p]) =>
          (
            p.allocations.find((row) => row.symbol === symbol)
              ?.weight_percent ?? 0
          ).toFixed(2),
        ),
      ]),
    ].entries()) {
      const row = document.createElement("tr");
      for (const text of cells) {
        const cell = document.createElement(i === 0 ? "th" : "td");
        if (i === 0) cell.scope = "col";
        cell.textContent = text;
        row.append(cell);
      }
      allocationTable.append(row);
    }
    const c = report.portfolios.current.metrics,
      a = report.portfolios.alternative?.metrics;
    $("difference").textContent = a
      ? `Alternative − current (percentage points, not percent change): ${((a.total_return - c.total_return) * 100).toFixed(2)} percentage points of total return; ${((a.max_drawdown - c.max_drawdown) * 100).toFixed(2)} percentage points of maximum drawdown. Historical comparison only.`
      : "Alternative comparison disabled.";
    $("coverage").textContent = JSON.stringify(
      {
        requested: report.requested,
        coverage: report.coverage,
        excluded_dates: report.excluded_dates,
        provenance: report.dataset,
      },
      null,
      2,
    );
    $("assumptions").replaceChildren();
    for (const s of report.assumptions) {
      const li = document.createElement("li");
      li.textContent = s;
      $("assumptions").append(li);
    }
  }
  $("inspect").oninput = () => inspect(Number($("inspect").value));
  $("riskInspect").oninput = () => inspect(Number($("riskInspect").value));
  $("allocationView").onchange = allocationChart;
  $("interpret").onclick = () => {
    if ($("interpret").disabled || requests.busy("commentary")) return;
    const id = report.analysis_id;
    requests.run(
      "commentary",
      (signal) => post("/dashboard/interpret", { analysis_id: id }, signal),
      {
        started: () => {
          sync();
          $("aiStatus").textContent =
            "Generating commentary… This may take about a minute.";
          $("commentary").replaceChildren();
        },
        success: (data) => {
          $("aiStatus").textContent = data.message;
          for (const [topic, text] of Object.entries(data.sections || {})) {
            const section = document.createElement("section"),
              heading = document.createElement("h3");
            heading.textContent = topic;
            section.append(heading);
            const detail = data.section_details?.[topic];
            const prose = document.createElement("p");
            prose.textContent = detail?.summary || text;
            section.append(prose);
            if (detail) {
              const facts = document.createElement("ul");
              facts.className = "verified-facts";
              for (const fact of detail.facts) {
                const li = document.createElement("li");
                li.textContent = `${fact.label}: ${fact.value}`;
                facts.append(li);
              }
              section.append(facts);
            }
            $("commentary").append(section);
          }
        },
        error: (error) => {
          $("aiStatus").textContent = error.message;
        },
        settled: sync,
      },
    );
  };
  $("printReport").onclick = () => {
    if (!stale && report) window.print();
  };
  let observedWidth = 0;
  new ResizeObserver((entries) => {
    const width = entries[0].contentRect.width;
    if (width > 0 && width !== observedWidth) {
      observedWidth = width;
      redrawCharts();
    }
  }).observe($("exploreStage"));

  let activeView = "overview";
  function redrawCharts() {
    if (!report || $("exploreStage").hidden) return;
    if (!$("overviewView").hidden) chart("performance", "index");
    if (!$("riskView").hidden) chart("drawdown", "drawdown");
  }
  function showWorkspace(stage, view = activeView) {
    $("buildStage").hidden = stage !== "build";
    $("exploreStage").hidden = stage === "build";
    for (const [id, active] of [
      ["navBuild", stage === "build"],
      ["navExplore", stage !== "build" && view !== "notes"],
      ["navNotes", stage !== "build" && view === "notes"],
    ]) {
      $(id).classList.toggle("active", active);
      if (active) $(id).setAttribute("aria-current", "step");
      else $(id).removeAttribute("aria-current");
    }
    activeView = view;
    for (const name of ["overview", "risk", "scenarios", "notes"]) {
      const button = $("tab" + name[0].toUpperCase() + name.slice(1));
      button.setAttribute("aria-selected", String(name === view));
      button.tabIndex = name === view ? 0 : -1;
      $(name + "View").hidden = name !== view;
    }
    requestAnimationFrame(redrawCharts);
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  for (const name of ["overview", "risk", "scenarios", "notes"]) {
    const button = $("tab" + name[0].toUpperCase() + name.slice(1));
    button.onclick = () => showWorkspace("explore", name);
    button.onkeydown = (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key))
        return;
      event.preventDefault();
      const tabs = ["overview", "risk", "scenarios", "notes"];
      let index = tabs.indexOf(name);
      index =
        event.key === "Home"
          ? 0
          : event.key === "End"
            ? 3
            : (index + (event.key === "ArrowRight" ? 1 : -1) + 4) % 4;
      showWorkspace("explore", tabs[index]);
      $("tab" + tabs[index][0].toUpperCase() + tabs[index].slice(1)).focus();
    };
  }
  $("navBuild").onclick = () => showWorkspace("build");
  $("editMix").onclick = () => {
    showWorkspace("build");
    $("buildTitle").focus({ preventScroll: true });
  };
  $("navExplore").onclick = () => showWorkspace("explore", "overview");
  $("navNotes").onclick = () => showWorkspace("explore", "notes");
  $("quickStart").onclick = () => {
    reset();
    $("calculate").click();
  };
  $("equalWeight").onclick = () => {
    if (!rows.length) return;
    rows.forEach(
      (row, index) =>
        (row.current =
          index === rows.length - 1
            ? Number(
                (
                  100 -
                  ((rows.length - 1) * Math.floor(10000 / rows.length)) / 100
                ).toFixed(2),
              )
            : Math.floor(10000 / rows.length) / 100),
    );
    edit();
    dirty();
  };
  function mixPreview(total) {
    const palette = [
      "#3157ff",
      "#83918b",
      "#b66c2e",
      "#d1ad67",
      "#8f81a3",
      "#679f91",
      "#c38a95",
      "#9aa66d",
      "#708789",
      "#a28970",
    ];
    let angle = 0;
    const wedges = [];
    $("mixLegend").replaceChildren();
    rows.forEach((row, i) => {
      const value = Math.max(0, Number(row.current) || 0);
      const start = angle;
      angle += (value / Math.max(100, total)) * 360;
      wedges.push(`${palette[i]} ${start}deg ${angle}deg`);
      const line = document.createElement("div");
      line.className = "mix-ingredient";
      const label = document.createElement("span"),
        dot = document.createElement("i"),
        weight = document.createElement("b");
      dot.style.background = palette[i];
      label.append(
        dot,
        document.createTextNode(canonicalSymbol(row.symbol) || "New stock"),
      );
      weight.textContent = value.toFixed(2) + "%";
      line.append(label, weight);
      $("mixLegend").append(line);
    });
    wedges.push(`#edf0ea ${angle}deg 360deg`);
    $("mixRing").style.background = `conic-gradient(${wedges.join(",")})`;
    $("mixRing").setAttribute(
      "aria-label",
      `Current allocation totals ${total.toFixed(2)} percent across ${rows.length} stocks`,
    );
    $("mixTotal").textContent = total.toFixed(total % 1 ? 2 : 0) + "%";
    $("mixCount").textContent =
      rows.length + (rows.length === 1 ? " stock" : " stocks");
  }
  reset();
  if (new URLSearchParams(window.location?.search || "").get("example") === "1")
    $("quickStart").click();

  window.addEventListener("beforeprint", () => {
    if (!report || stale) return;
    for (const [id, key] of [
      ["performance", "index"],
      ["drawdown", "drawdown"],
    ]) {
      const panel = $(id).closest(".report-view");
      const hidden = panel.hidden;
      panel.hidden = false;
      chart(id, key);
      panel.hidden = hidden;
    }
  });
  window.addEventListener("afterprint", redrawCharts);
}

try {
  initializeDashboard();
} catch (error) {
  controllerFailure(error);
}
