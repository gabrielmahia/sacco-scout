# Data status (sacco-scout)

**Nothing in `data/` has been independently verified.** Read this before using or citing any figure.

- These files were added in a single "initial release" commit on 2026-03-10 and never revised. No source URL, report page, or verification record exists in this repository: the `source` column names a publisher, not a document.
- At creation every row carried `verified = confirmed`, and a test required it. No evidence supports that. On 2026-10-05 every such flag was changed to `unverified`, and the test now requires that a row may claim `confirmed` only if `data/VERIFICATION_LOG.csv` records evidence for it (`file,row_key,evidence_url,verified_by,verified_on`). The log is empty.
- Financial figures (assets, deposits, dividends, loan rates, NPL and capital-adequacy ratios) describe named financial institutions. Do not use them to choose where to save or borrow without checking the current SASRA report.

To verify a row: open the cited report, check the figure, add a line to `VERIFICATION_LOG.csv` with the URL, your name and the date, then set the row's `verified` to `confirmed`.
