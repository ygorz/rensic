import pack from "./knownEntities.json";

export type EntityCategory = "exchange" | "gambling" | "mixer" | "person" | "protocol" | "sanctions" | "shop";

export type EntityTier = "official" | "community";

export type KnownEntity = {
  chain: string;
  address: string;
  name: string;
  category: EntityCategory;
  secondaryCategory?: EntityCategory;
  source: string;
  sourceUrl: string;
  tier: EntityTier;
};

export const KNOWN_ENTITIES: KnownEntity[] = pack as KnownEntity[];

const BY_HEX: Record<string, KnownEntity> = {};
for (const row of KNOWN_ENTITIES) {
  BY_HEX[row.address.toLowerCase()] = row;
}

function hexOf(id: string | undefined): string | undefined {
  if (!id) {
    return undefined;
  }
  const raw = id.includes(":") ? id.split(":").pop()! : id;
  const h = raw.trim().toLowerCase();
  return /^0x[0-9a-f]{40}$/.test(h) ? h : undefined;
}

export function lookupKnownEntity(id: string | undefined): KnownEntity | undefined {
  const hex = hexOf(id);
  if (!hex) {
    return undefined;
  }
  return BY_HEX[hex];
}

export function entityCategories(row: KnownEntity | undefined): EntityCategory[] {
  if (!row) {
    return [];
  }
  const out: EntityCategory[] = [row.category];
  if (row.secondaryCategory && row.secondaryCategory !== row.category) {
    out.push(row.secondaryCategory);
  }
  return out;
}

export function isOfficialEntity(row: KnownEntity | undefined): boolean {
  return Boolean(row) && (row!.tier ?? "official") === "official";
}

export function isCommunityEntity(row: KnownEntity | undefined): boolean {
  return Boolean(row) && row!.tier === "community";
}

export function seedExposureLine(
  rows: { addressId?: string; membershipRole?: string; hopDistance?: number }[],
): string {
  const hop1 = rows.filter((r) => {
    const role = (r.membershipRole ?? "").toLowerCase();
    return role !== "seed" && r.hopDistance !== 0;
  });
  let mixer: KnownEntity | undefined;
  let sdn: KnownEntity | undefined;
  let other: KnownEntity | undefined;
  for (const r of hop1) {
    const ent = lookupKnownEntity(r.addressId);
    if (!ent) {
      continue;
    }
    const cats = entityCategories(ent);
    if (!mixer && cats.includes("mixer")) {
      mixer = ent;
    } else if (!sdn && cats.includes("sanctions")) {
      sdn = ent;
    } else if (!other) {
      other = ent;
    }
  }
  if (mixer) {
    return `Touched a mixer (${mixer.name})`;
  }
  if (sdn) {
    return "Touched a sanctions address";
  }
  if (other) {
    return touchedLine(other.category, other.name);
  }
  return "No public names on the addresses touched.";
}

function touchedLine(category: string, name: string): string {
  if (category === "exchange") {
    return `Touched an exchange (${name})`;
  }
  if (category === "gambling") {
    return `Touched a gambling address (${name})`;
  }
  return `Touched a ${category} (${name})`;
}
