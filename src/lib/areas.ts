/** Home page grouping: the 10 service categories folded into three broad areas. */
import { t, type Lang } from './content';

const G = '/img/gallery/';

export const AREAS = [
  {
    id: 'machinery',
    categories: ['machinery', 'parts-processing', 'workplace-measurements'],
    photo: G + 'engineer-work-at-robotic-arm-factory-2026-03-10-01-10-42-utc.jpg',
    title: (l: Lang) => t(l, 'Maszyny i pomiary', 'Machinery and measurements'),
    line: (l: Lang) =>
      t(l, 'Audyty, dostosowanie i pomiary parków maszynowych.', 'Audits, compliance and measurement of machine parks.'),
  },
  {
    id: 'safety',
    categories: ['ohs', 'fire-safety', 'adr'],
    photo: G + 'fire-fighter-team-on-training-with-gas-and-oil-fir-2026-03-09-09-01-40-utc.jpg',
    title: (l: Lang) => t(l, 'BHP, ppoż. i ADR', 'Health, safety and fire'),
    line: (l: Lang) =>
      t(l, 'Outsourcing BHP, ochrona przeciwpożarowa i transport.', 'OHS outsourcing, fire protection and transport.'),
  },
  {
    id: 'people',
    categories: ['environment', 'occupational-medicine', 'employment-agency', 'iso'],
    photo: G + 'scientists-working-in-the-laboratory-2026-01-08-23-49-36-utc.jpg',
    title: (l: Lang) => t(l, 'Środowisko, ludzie i systemy', 'Environment, people and systems'),
    line: (l: Lang) =>
      t(l, 'Laboratorium, medycyna pracy, rekrutacja i ISO.', 'Laboratory, occupational medicine, staffing and ISO.'),
  },
] as const;
