# Vercel deployment

Later restoration/deployment work (November 2026), separate from the collaborative 2025 internship.

The Flask app is the Vercel entry point. Python 3.12 is pinned. Runtime dependencies are in requirements.txt. No paid plan or external database is required for this small demonstration; account eligibility and platform quotas still apply.

`data/local/` stays Git-ignored. This CLI deployment privately bundles the retained saved snapshot and ETF cache inside the Python function, never a public static prices directory. Retain these files privately for reproducibility and check provider terms before further data distribution. A Git-only deployment without preparing/restoring those files will show explicit missing-data errors. Do not upload keys or original credential-bearing notebooks.

Vercel copies the bundle's local data to an instance-specific temporary directory. Newly retrieved histories are ephemeral and can disappear on cold starts; Yahoo can reject cloud-hosted requests. The saved example remains the preferred demonstration. This is not durable portfolio storage.

Set ANALYSIS_SIGNING_KEY to a private random server secret. Signed, expiring interpretation facts let separate instances validate the same analysis without trusting client-supplied metrics. Signed tokens are readable, not encrypted; they contain only the calculated report facts already returned to that browser. No user account or stored portfolio database is provided.

GEMINI_API_KEY is optional and server-only. If configured, the public interpretation endpoint consumes that project's quota, so leave it unset for the initial free-only deployment. GEMINI_MODEL defaults to gemini-3.5-flash-lite. No key from chat is reused. Use a confirmed free API project if enabling this later; the app cannot inspect billing eligibility.

Deploy from this prepared local checkout with `vercel --prod`. A fresh GitHub import requires online dataset preparation or privately restoring the saved files before build. Credentials and data are not committed. Follow the official [Flask](https://vercel.com/docs/frameworks/backend/flask) and [Python runtime](https://vercel.com/docs/functions/runtimes/python) deployment guidance.
