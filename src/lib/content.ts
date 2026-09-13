/**
 * Single entry point for site content. Pages never import JSON directly —
 * they call these helpers, so the JSON layout (or a future CMS) can change in one place.
 */
import { z } from 'zod';

export const LANGS = ['pl', 'en'] as const;
export type Lang = (typeof LANGS)[number];

const Block = z.discriminatedUnion('type', [
  z.object({ type: z.literal('heading'), level: z.number(), text: z.string(), eyebrow: z.string().optional() }),
  z.object({ type: z.literal('paragraph'), text: z.string() }),
  z.object({ type: z.literal('list'), ordered: z.boolean(), items: z.array(z.string()) }),
  z.object({ type: z.literal('image'), src: z.string(), alt: z.string() }),
  z.object({ type: z.literal('cta'), label: z.string(), href: z.string() }),
]);
export type Block = z.infer<typeof Block>;

const Meta = z.object({ title: z.string(), description: z.string(), sourceUrl: z.string().optional() });

const Site = z.object({
  brand: z.object({ name: z.string(), logo: z.string(), colors: z.record(z.string()) }),
  contact: z.object({ email: z.string(), phone: z.string(), address: z.string() }),
  social: z.record(z.string()),
  languages: z.array(z.enum(LANGS)),
  defaultLanguage: z.enum(LANGS),
  nav: z.record(z.array(z.object({ id: z.string(), label: z.string(), href: z.string() }))),
});

const Home = Meta.extend({
  hero: z.object({ headline: z.string(), ctas: z.array(z.object({ label: z.string(), href: z.string() })) }),
  asia: z.object({ headline: z.string(), cta: z.string(), lines: z.array(z.string()) }),
  services: z.object({
    eyebrow: z.string(), headline: z.string(),
    cards: z.array(z.object({ title: z.string(), text: z.string() })),
  }),
  maturity: z.object({
    eyebrow: z.string(), headline: z.string(),
    axis: z.object({ high: z.string(), label: z.string(), low: z.string() }),
    stages: z.array(z.object({ name: z.string(), text: z.string(), management: z.string() })),
  }),
  noBlame: z.object({ headline: z.string(), phrases: z.array(z.string()) }),
  closing: z.object({
    eyebrow: z.string(), headline: z.string(),
    values: z.array(z.object({ title: z.string(), text: z.string() })),
    chain: z.array(z.string()),
  }),
});

const Page = Meta.extend({ blocks: z.array(Block) });

const ServiceIndex = z.object({
  categories: z.array(z.object({ id: z.string(), label: z.string(), services: z.array(z.string()) })),
});

const Service = z.object({
  id: z.string(), category: z.string(), hasPage: z.boolean(),
  title: z.string(), menuLabel: z.string().optional(), description: z.string().optional(),
  sourceUrl: z.string().optional(), blocks: z.array(Block),
});
export type Service = z.infer<typeof Service>;

// eager glob so everything is validated at build time
const files = import.meta.glob('../content/**/*.json', { eager: true, import: 'default' }) as Record<string, unknown>;

function load<T>(path: string, schema: z.ZodType<T>): T {
  const raw = files[`../content/${path}`];
  if (raw === undefined) throw new Error(`content file missing: src/content/${path}`);
  const r = schema.safeParse(raw);
  if (!r.success) throw new Error(`content invalid: src/content/${path}\n${r.error.message}`);
  return r.data;
}

export const site = load('site.json', Site);
export const getHome = (lang: Lang) => load(`${lang}/home.json`, Home);
export const getPage = (lang: Lang, id: 'about' | 'services' | 'gallery' | 'clients' | 'contact') => load(`${lang}/${id === 'services' ? 'services-page' : id}.json`, Page);
export const getServiceIndex = (lang: Lang) => load(`${lang}/services.json`, ServiceIndex);
export const getService = (lang: Lang, id: string) => load(`${lang}/services/${id}.json`, Service);

/** all services that have their own detail page, in category order */
export function listServices(lang: Lang): (Service & { categoryLabel: string })[] {
  const idx = getServiceIndex(lang);
  return idx.categories.flatMap((c) =>
    c.services.map((id) => ({ ...getService(lang, id), categoryLabel: c.label })).filter((s) => s.hasPage),
  );
}

export const t = (lang: Lang, pl: string, en: string) => (lang === 'pl' ? pl : en);
export const otherLang = (lang: Lang): Lang => (lang === 'pl' ? 'en' : 'pl');
