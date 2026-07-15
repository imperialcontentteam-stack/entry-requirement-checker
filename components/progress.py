"""Progress components used by document processing and Run Check."""

import html

import streamlit as st


class StepProgress:
    """Progress bar and live status card across a fixed number of steps."""

    def __init__(self, total_steps: int, subject: str = ""):
        self.total = max(1, total_steps)
        self.subject = subject
        self.bar = st.progress(0.0)
        self.status = st.empty()

    def step(self, n: int, label: str):
        pct = int((n - 1) / self.total * 100)
        remaining = self.total - (n - 1)
        subject = f" · {html.escape(self.subject)}" if self.subject else ""
        self.status.markdown(
            f'<div class="progress-status"><b>Step {n} of {self.total}</b>'
            f' · {html.escape(label)}{subject}<br>'
            f'{pct}% complete · {remaining} step(s) remaining</div>',
            unsafe_allow_html=True,
        )
        self.bar.progress((n - 1) / self.total)

    def done(self, message: str = "Complete"):
        self.bar.progress(1.0)
        self.status.markdown(
            f'<div class="progress-status"><b>✓ {html.escape(message)}</b>'
            f' · 100% complete</div>',
            unsafe_allow_html=True,
        )


class BulkProgress:
    """Progress indicator for a sequence of specification documents."""

    def __init__(self, total: int):
        self.total = max(1, total)
        self.bar = st.progress(0.0)
        self.status = st.empty()
        self.done_count = 0

    def update(self, label: str):
        self.done_count += 1
        pct = int(self.done_count / self.total * 100)
        self.status.markdown(
            f'<div class="progress-status"><b>Processing {self.done_count} of '
            f'{self.total}</b> · {pct}%<br>{html.escape(label)}</div>',
            unsafe_allow_html=True,
        )
        self.bar.progress(self.done_count / self.total)

    def finish(self):
        self.bar.progress(1.0)
        self.status.empty()
