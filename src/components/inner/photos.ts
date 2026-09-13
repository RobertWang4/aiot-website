/** Header photography, picked per page and per service category. Generated stock set in public/img/stock/. */
const S = '/img/stock/';

export const pagePhoto = {
  about: S + 'header-building.jpg',
  services: S + 'header-conveyor.jpg',
  gallery: S + 'header-robot-detail.jpg',
  clients: S + 'header-forklift.jpg',
  contact: S + 'header-dock.jpg',
} as const;

const byCategory: Record<string, string> = {
  machinery: S + 'header-robot-arm.jpg',
  environment: S + 'header-building.jpg',
  'parts-processing': S + 'header-robot-arm.jpg',
  'occupational-medicine': S + 'area-engineers.jpg',
  'employment-agency': S + 'header-team.jpg',
  'workplace-measurements': S + 'area-control-room.jpg',
  ohs: S + 'header-amr.jpg',
  'fire-safety': S + 'header-dock.jpg',
  iso: S + 'area-control-room.jpg',
  adr: S + 'header-conveyor.jpg',
};

export const categoryPhoto = (id: string) => byCategory[id] ?? pagePhoto.services;
