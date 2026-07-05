// Static roster for the pre-debate hero (mirrors backend/personas.py). Once a debate
// starts, the live agent list from the debate_start event replaces this.
export const DEFAULT_AGENTS = [
  { id: 'brand_manager', name: 'Priya', role: 'Brand Manager', color: 'brand' },
  { id: 'media_manager', name: 'Rohan', role: 'Media Manager', color: 'media-mgr' },
  { id: 'scriptwriter', name: 'Sana', role: 'Scriptwriter', color: 'script' },
  { id: 'copywriter', name: 'Dev', role: 'Copywriter', color: 'copy' },
  { id: 'media_planner', name: 'Mira', role: 'Media Planner', color: 'planner' },
];
