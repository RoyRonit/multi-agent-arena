import { useEffect, useRef, useState } from 'react';

// An ongoing research-lab section (not a product roadmap). Lives below the hero roster,
// pre-debate only. LIVE is the one real link; the rest are visually identical but inert.
const EXPERIMENTS = [
  {
    n: '01',
    title: 'The Roundtable',
    status: 'LIVE',
    href: '#roundtable',
    thesis: 'Five marketing specialists debate one brief with budgets and rewards.',
  },
  {
    n: '02',
    title: "The Devil's Advocate",
    status: 'IN BUILD',
    thesis:
      'A single agent whose only job is to attack the current best answer until it survives or breaks.',
  },
  {
    n: '03',
    title: 'The Silent Auction',
    status: 'RESEARCH',
    thesis:
      "Agents bid credits to speak; the market decides who's worth hearing on which question.",
  },
  {
    n: '04',
    title: 'The Jury',
    status: 'RESEARCH',
    thesis:
      'Twelve specialists deliberate on a single decision; unanimity or hung. Studying disagreement, not consensus.',
  },
  {
    n: '05',
    title: 'The Apprentice',
    status: 'QUEUED',
    thesis:
      'A weak model learns to argue by watching stronger ones debate and imitating the winners.',
  },
  {
    n: '06',
    title: 'The Long Table',
    status: 'QUEUED',
    thesis:
      'Debates that persist across sessions — agents remember old grudges and unresolved threads.',
  },
];

function ExperimentCard({ n, title, status, thesis, href }) {
  const inner = (
    <>
      <div className="exp-top">
        <span className="exp-num mono">{n}</span>
        <span className={`exp-tag mono status-${status.toLowerCase().replace(' ', '-')}`}>
          {status}
        </span>
      </div>
      <h3 className="exp-title">{title}</h3>
      <p className="exp-thesis">{thesis}</p>
    </>
  );
  return href ? (
    <a className="exp-card is-link" href={href}>
      {inner}
    </a>
  ) : (
    <div className="exp-card" aria-disabled="true">
      {inner}
    </div>
  );
}

export default function Experiments() {
  const ref = useRef(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShown(true);
          io.disconnect();
        }
      },
      { threshold: 0.12 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <section
      ref={ref}
      className={`experiments${shown ? ' in' : ''}`}
      aria-label="Upcoming experiments"
    >
      <div className="eyebrow micro-caps">Research · Ongoing</div>
      <h2 className="exp-headline">Experiments in multi-agent architectures</h2>
      <p className="exp-dek">
        Small, visible studies in how specialist agents produce better answers by
        disagreeing than any single model does by averaging.
      </p>
      <div className="exp-grid">
        {EXPERIMENTS.map((x) => (
          <ExperimentCard key={x.n} {...x} />
        ))}
      </div>
    </section>
  );
}
