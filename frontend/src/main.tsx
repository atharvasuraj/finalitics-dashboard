import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';

// The original App/components remain as historical reference. Do not run their
// unverified analysis actions against the restored demonstration backend.
createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <main style={{maxWidth: 760, margin: '48px auto', padding: 24, fontFamily: 'sans-serif', lineHeight: 1.6}}>
      <h1>Legacy React interface · unverified</h1>
      <p>This 2025 team interface is preserved as reference material. Its analysis actions are disabled in the restored demonstration.</p>
      <p><a href="http://127.0.0.1:5001/portfolio-analyser">Open the supported Flask historical portfolio analyser</a></p>
      <p>The supported demo uses saved stock prices, explicit buy-and-hold assumptions, and no forecasting or LLM key.</p>
    </main>
  </React.StrictMode>
);
