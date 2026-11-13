// Formats français (virgule décimale, dates en toutes lettres), sans dépendre de la langue du téléphone.
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

export function nombreFr(n: number | null | undefined, decimales: number): string {
  if (n == null) return '?';
  return n.toFixed(decimales).replace('.', ',');
}

/** « 2026-09-20 » → « 20 septembre 2026 » (ou « 20 septembre » sans l'année). */
export function dateFr(iso: string | null | undefined, avecAnnee = true): string {
  const m = iso?.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return '?';
  const jour = Number(m[3]);
  return `${jour === 1 ? '1er' : jour} ${MOIS[Number(m[2]) - 1]}${avecAnnee ? ` ${m[1]}` : ''}`;
}
