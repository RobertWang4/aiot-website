/** Header photography, picked per page and per service category. */
const G = '/img/gallery/';

export const pagePhoto = {
  about: G + 'portrait-of-confident-factory-manager-with-diverse-2026-01-09-11-12-24-utc.jpg',
  services: G + 'engineer-work-at-robotic-arm-factory-2026-03-10-01-10-42-utc.jpg',
  gallery: G + 'close-up-view-on-gear-mechanism-of-old-combine-har-2026-01-11-09-30-57-utc.jpg',
  clients: G + 'team-and-portrait-of-engineering-employees-standin-2026-03-09-03-24-39-utc.jpg',
  contact: G + 'factory-executives-discuss-solar-panel-research-an-2026-01-11-10-56-20-utc.jpg',
} as const;

const byCategory: Record<string, string> = {
  machinery: G + 'robot-welding-technology-in-factory-2026-01-08-00-11-27-utc.jpg',
  environment: G + 'inspector-examination-of-photovoltaic-modules-usin-2026-01-09-00-13-33-utc.jpg',
  'parts-processing': G + 'mechanics-engineer-operating-lathe-machine-for-met-2026-01-07-07-03-58-utc.jpg',
  'occupational-medicine': G + 'man-and-woman-doctors-are-standing-together-indoor-2026-01-09-00-02-25-utc.jpg',
  'employment-agency': G + 'diverse-people-in-a-seminar-2026-01-07-07-26-02-utc.jpg',
  'workplace-measurements': G + '53732-machinery-in-laboratory-2026-01-09-11-39-55-utc.jpg',
  ohs: G + 'emergency-machine-stop-button-2026-01-09-10-40-43-utc.jpg',
  'fire-safety': G + 'fire-fighter-team-on-training-with-gas-and-oil-fir-2026-03-09-09-01-40-utc.jpg',
  iso: G + 'speaker-ready-to-answer-question-on-conference-2026-01-07-06-57-16-utc.jpg',
  adr: G + 'modern-conveyor-system-with-boxes-in-motion-2026-01-08-05-12-48-utc.jpg',
};

export const categoryPhoto = (id: string) => byCategory[id] ?? pagePhoto.services;
