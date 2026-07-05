// Shown when the user tries to leave a debate they haven't downloaded. Nothing is
// persisted for the viewer, so this is the one chance to keep the transcript.
export default function LeaveNudge({ onDownload, onLeave, onCancel }) {
  return (
    <div className="verdict-backdrop" onClick={onCancel}>
      <div className="nudge-card" onClick={(e) => e.stopPropagation()}>
        <div className="micro-caps">Before you go</div>
        <h2>Nothing here is saved.</h2>
        <p className="nudge-text">
          Leaving returns you to the start and clears this debate — the transcript and
          verdict are gone. Download it first?
        </p>
        <div className="verdict-actions">
          <button className="text-btn" onClick={onLeave}>
            Leave without saving
          </button>
          <button className="pill pill-sm" onClick={onDownload}>
            Download transcript
          </button>
        </div>
      </div>
    </div>
  );
}
