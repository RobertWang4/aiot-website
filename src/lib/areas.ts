/** Home page grouping: the 10 service categories folded into three broad areas. */
import { t, type Lang } from './content';

const G = '/img/stock/';

export const AREAS = [
  {
    id: 'machinery',
    categories: ['machinery', 'parts-processing', 'workplace-measurements'],
    photo: G + 'area-asrs.jpg',
    title: (l: Lang) => t(l, 'Maszyny i pomiary', 'Machinery and measurements'),
    line: (l: Lang) =>
      t(l, 'Audyty, dostosowanie i pomiary parków maszynowych.', 'Audits, compliance and measurement of machine parks.'),
  },
  {
    id: 'safety',
    categories: ['ohs', 'fire-safety', 'adr'],
    photo: G + 'area-engineers.jpg',
    title: (l: Lang) => t(l, 'BHP, ppoż. i ADR', 'Health, safety and fire'),
    line: (l: Lang) =>
      t(l, 'Outsourcing BHP, ochrona przeciwpożarowa i transport.', 'OHS outsourcing, fire protection and transport.'),
  },
  {
    id: 'people',
    categories: ['environment', 'occupational-medicine', 'employment-agency', 'iso'],
    photo: G + 'area-control-room.jpg',
    title: (l: Lang) => t(l, 'Środowisko, ludzie i systemy', 'Environment, people and systems'),
    line: (l: Lang) =>
      t(l, 'Laboratorium, medycyna pracy, rekrutacja i ISO.', 'Laboratory, occupational medicine, staffing and ISO.'),
  },
] as const;
