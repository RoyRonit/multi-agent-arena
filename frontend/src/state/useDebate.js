// EventSource -> useReducer. Single source of truth for the whole UI (FRONTEND §7).
import { useReducer, useRef, useCallback } from 'react';

const initial = {
  status: 'idle', // idle | running | complete | error
  error: null,
  debateId: null,
  brief: '',
  round: 0,
  totalRounds: 0,
  agents: [],
  agentById: {},
  budgets: {}, // { id: { balance, muted } }
  maxBalance: 1000,
  activeAgent: null,
  transcript: [], // { key, agent_id, name, role, round, text, cost, streaming, skipped }
  rounds: [], // round records
  novelty: {}, // { agent_id: [n per round] }
  verdict: null,
  tickers: {}, // { agent_id: { kind, amount, key } }
  rebuttal: null, // { from, to, key }
  log: [],
};

let _k = 0;
const nextKey = () => `${Date.now()}-${_k++}`;

function ts() {
  return new Date().toLocaleTimeString('en-GB');
}

function detectRebuttal(text, speakerId, agents) {
  if (!text) return null;
  const lower = text.toLowerCase();
  for (const a of agents) {
    if (a.id === speakerId) continue;
    if (lower.includes(a.name.toLowerCase())) {
      return { from: speakerId, to: a.id, key: nextKey() };
    }
  }
  return null;
}

function reducer(state, ev) {
  switch (ev.type) {
    case 'debate_start': {
      const agentById = {};
      ev.agents.forEach((a) => (agentById[a.id] = a));
      const balances = Object.values(ev.budgets || {}).map((b) => b.balance);
      const maxBalance = balances.length ? Math.max(...balances) : 1000;
      return {
        ...initial,
        status: 'running',
        debateId: ev.debate_id || null,
        brief: ev.brief,
        totalRounds: ev.rounds,
        agents: ev.agents,
        agentById,
        budgets: ev.budgets,
        maxBalance,
        log: [`${ts()}  debate  start  ${ev.agents.length} agents · ${ev.rounds} rounds`],
      };
    }

    case 'round_start':
      return {
        ...state,
        round: ev.round,
        log: [...state.log, `${ts()}  round  ${ev.round}/${ev.total}  begin`],
      };

    case 'turn_start': {
      const a = state.agentById[ev.agent] || {};
      const entry = {
        key: nextKey(),
        agent_id: ev.agent,
        name: a.name,
        role: a.role,
        round: ev.round,
        text: '',
        cost: null,
        streaming: true,
        skipped: false,
      };
      return { ...state, activeAgent: ev.agent, transcript: [...state.transcript, entry] };
    }

    case 'turn_delta': {
      const t = [...state.transcript];
      for (let i = t.length - 1; i >= 0; i--) {
        if (t[i].agent_id === ev.agent && t[i].streaming) {
          t[i] = { ...t[i], text: t[i].text + ev.chunk };
          break;
        }
      }
      return { ...state, transcript: t };
    }

    case 'turn': {
      const t = [...state.transcript];
      for (let i = t.length - 1; i >= 0; i--) {
        if (t[i].agent_id === ev.agent && t[i].streaming) {
          t[i] = { ...t[i], text: ev.text, cost: ev.cost, streaming: false };
          break;
        }
      }
      const rebuttal = detectRebuttal(ev.text, ev.agent, state.agents) || state.rebuttal;
      return {
        ...state,
        transcript: t,
        budgets: ev.budgets || state.budgets,
        rebuttal,
        tickers: {
          ...state.tickers,
          [ev.agent]: { kind: 'charge', amount: -ev.cost, key: nextKey() },
        },
        log: [
          ...state.log,
          `${ts()}  ${ev.agent}  charge  −${ev.cost}  ▸ ${ev.balance}`,
        ],
      };
    }

    case 'turn_skipped': {
      const a = state.agentById[ev.agent] || {};
      return {
        ...state,
        transcript: [
          ...state.transcript,
          {
            key: nextKey(),
            agent_id: ev.agent,
            name: a.name,
            role: a.role,
            round: ev.round,
            text: 'Silenced — no budget to speak.',
            skipped: true,
            streaming: false,
          },
        ],
        log: [...state.log, `${ts()}  ${ev.agent}  skip  bankrupt`],
      };
    }

    case 'round_result': {
      const novelty = { ...state.novelty };
      ev.scores.forEach((s) => {
        novelty[s.agent] = [...(novelty[s.agent] || []), s.novelty];
      });
      const tickers = { ...state.tickers };
      Object.entries(ev.rewards || {}).forEach(([id, amt]) => {
        tickers[id] = { kind: 'reward', amount: amt, key: nextKey() };
      });
      Object.entries(ev.fines || {}).forEach(([id, amt]) => {
        tickers[id] = { kind: 'fine', amount: -amt, key: nextKey() };
      });
      const winName = state.agentById[ev.winner]?.name || ev.winner || '—';
      return {
        ...state,
        rounds: [...state.rounds, ev],
        budgets: ev.budgets || state.budgets,
        novelty,
        tickers,
        activeAgent: null,
        log: [
          ...state.log,
          `${ts()}  round  ${ev.round}  settled  win ${winName}`,
        ],
      };
    }

    case 'verdict':
      return { ...state, verdict: { text: ev.text, credits: ev.credits || [] } };

    case 'debate_early_end':
      return { ...state, log: [...state.log, `${ts()}  debate  early end  ${ev.reason}`] };

    case 'debate_end':
      return { ...state, status: 'complete', activeAgent: null };

    case 'error':
      return { ...state, status: 'error', error: ev.message, activeAgent: null };

    case 'reset':
      return initial;

    default:
      return state;
  }
}

export function useDebate() {
  const [state, dispatch] = useReducer(reducer, initial);
  const esRef = useRef(null);

  // Returns { ok, status, message }. On gate failure (401) we deliberately do NOT set
  // the global error state, so the user stays on the hero and gets an inline hint.
  const start = useCallback(async (brief, rounds, phrase) => {
    if (esRef.current) esRef.current.close();
    const res = await fetch('/api/debate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(phrase ? { 'x-access-phrase': phrase } : {}),
      },
      body: JSON.stringify({ brief, rounds }),
    });
    if (!res.ok) {
      let message = `Couldn't start debate (${res.status}).`;
      try {
        message = (await res.json()).detail || message;
      } catch (_) {
        /* keep default */
      }
      if (res.status !== 401 && res.status !== 429) {
        dispatch({ type: 'error', message });
      }
      return { ok: false, status: res.status, message };
    }
    const { id } = await res.json();
    const es = new EventSource(`/api/debate/${id}/events`);
    esRef.current = es;
    es.onmessage = (e) => {
      try {
        dispatch(JSON.parse(e.data));
      } catch (_) {
        /* ignore keep-alives */
      }
    };
    es.onerror = () => {
      // Stream closes normally after debate_end; only surface if we never finished.
      es.close();
    };
    return { ok: true, status: 200 };
  }, []);

  const reset = useCallback(() => {
    if (esRef.current) esRef.current.close();
    esRef.current = null;
    dispatch({ type: 'reset' });
  }, []);

  return { state, start, reset };
}
