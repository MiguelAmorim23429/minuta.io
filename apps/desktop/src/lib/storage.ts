/**
 * Preferências de conveniência guardadas no browser (ex.: última pasta de destino).
 * Nunca guardar aqui dados dos clientes.
 */

const PREFIX = "minuta.io:";

export function loadPreference(key: string): string | null {
  try {
    return window.localStorage.getItem(PREFIX + key);
  } catch {
    return null;
  }
}

export function savePreference(key: string, value: string): void {
  try {
    window.localStorage.setItem(PREFIX + key, value);
  } catch {
    // Sem armazenamento disponível: a preferência simplesmente não é lembrada.
  }
}
