import { useState } from 'react';
import { useDebate } from './state/useDebate';
import Hero from './components/Hero';
import Table from './components/Table';
import AgentChip from './components/AgentChip';
import Transcript from './components/Transcript';
import Verdict from './components/Verdict';
import EventLog from './components/EventLog';
import LeaveNudge from './components/LeaveNudge';
import { DEFAULT_AGENTS } from './agents';

export default function App() {
  const { state, start, reset } = useDebate();
  const {
    status,
    debateId,
    agents,
    agentById,
    budgets,
    maxBalance,
    activeAgent,
    round,
    totalRounds,
    transcript,
    rounds,
    novelty,
    verdict,
    tickers,
    rebuttal,
    error,
    brief,
  } = state;

  const [downloaded, setDownloaded] = useState(false);
  const [showLeaveNudge, setShowLeaveNudge] = useState(false);

  const preDebate = status === 'idle';
  const roster = agents.length ? agents : DEFAULT_AGENTS;

  const exportTranscript = () => {
    if (debateId) {
      // Server-rendered markdown (single source of truth). Triggers a file download.
      const a = document.createElement('a');
      a.href = `/api/debate/${debateId}/transcript`;
      a.download = `roundtable-${debateId}.md`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } else {
      exportClientSide();
    }
    setDownloaded(true);
  };

  const exportClientSide = () => {
    let md = `# The Roundtable — Debate Transcript\n\n**Brief:** ${brief}\n\n`;
    let lastRound = 0;
    transcript.forEach((t) => {
      if (t.round !== lastRound) {
        md += `\n## Round ${t.round}\n\n`;
        lastRound = t.round;
      }
      md += `**${t.name} · ${t.role}:** ${t.text}\n\n`;
    });
    if (verdict) {
      md += `\n## Verdict\n\n${verdict.text}\n\n`;
      verdict.credits?.forEach((c) => (md += `- **${c.agent}** — ${c.argument}\n`));
    }
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'roundtable-transcript.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  const doReset = () => {
    setShowLeaveNudge(false);
    setDownloaded(false);
    reset();
  };

  // Going back loses the debate (nothing is persisted client-side). If there's
  // something worth keeping and it hasn't been downloaded, nudge first.
  const requestBack = () => {
    if (transcript.length && !downloaded) {
      setShowLeaveNudge(true);
    } else {
      doReset();
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <button
          className="wordmark micro-caps as-link"
          onClick={preDebate ? undefined : requestBack}
          title={preDebate ? undefined : 'Back to start'}
        >
          {preDebate ? 'The Roundtable' : '← The Roundtable'}
        </button>
        <span className="round-indicator micro-caps">
          {preDebate
            ? 'Ready'
            : status === 'complete'
            ? 'Complete'
            : `Round ${round || 1}/${totalRounds}`}
        </span>
      </header>

      {error && <div className="error-banner">⚠ {error}</div>}

      {preDebate ? (
        <Hero
          agents={roster}
          maxBalance={maxBalance}
          onConvene={(b, r, p) => start(b, r, p)}
        />
      ) : (
        <div className="stage">
          <div className="stage-left">
            <Table
              agents={agents}
              budgets={budgets}
              activeAgent={activeAgent}
              round={round}
              totalRounds={totalRounds}
              rebuttal={rebuttal}
            />
            <div className="chips">
              {agents.map((a) => (
                <AgentChip
                  key={a.id}
                  agent={a}
                  budget={budgets[a.id]}
                  max={maxBalance}
                  ticker={tickers[a.id]}
                />
              ))}
            </div>
            <EventLog log={state.log} />
          </div>

          <div className="stage-right">
            <Transcript
              transcript={transcript}
              rounds={rounds}
              agentById={agentById}
              novelty={novelty}
              totalRounds={totalRounds}
            />
          </div>
        </div>
      )}

      {verdict && (
        <Verdict
          verdict={verdict}
          agents={agents}
          onExport={exportTranscript}
          onNewDebate={requestBack}
        />
      )}

      {showLeaveNudge && (
        <LeaveNudge
          onDownload={() => {
            exportTranscript();
            doReset();
          }}
          onLeave={doReset}
          onCancel={() => setShowLeaveNudge(false)}
        />
      )}
    </div>
  );
}
