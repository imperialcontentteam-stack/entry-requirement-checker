"""Progress components: a step tracker for the Run Check workflow and a
bulk progress helper for spec processing."""

import streamlit as st


class StepProgress:
    """Progress bar + live status line across a fixed number of steps.
    Shows the current step, percentage complete and remaining steps."""

    def __init__(self, total_steps: int, subject: str = ""):
        self.total = max(1, total_steps)
        self.subject = subject
        self.bar = st.progress(0.0)
        self.status = st.empty()

    def step(self, n: int, label: str):
        pct = int((n - 1) / self.total * 100)
        remaining = self.total - (n - 1)
        self.status.markdown(
            f"**Step {n}/{self.total}** · {label}"
            + (f" — *{self.subject}*" if self.subject else "")
            + f"  \n{pct}% complete · {remaining} step(s) remaining"
        )
        self.bar.progress((n - 1) / self.total)

    def done(self, message: str = "Complete"):
        self.bar.progress(1.0)
        self.status.markdown(f"✅ **{message}** · 100% complete")


class BulkProgress:
    """Progress for a list of items (e.g. spec documents)."""

    def __init__(self, total: int):
        self.total = max(1, total)
        self.bar = st.progress(0.0)
        self.status = st.empty()
        self.done_count = 0

    def update(self, label: str):
        self.done_count += 1
        pct = int(self.done_count / self.total * 100)
        self.status.markdown(
            f"Processing **{self.done_count}/{self.total}** ({pct}%) · {label}")
        self.bar.progress(self.done_count / self.total)

    def finish(self):
        self.bar.progress(1.0)
        self.status.empty()
