/**
 * Validações locais que apenas **avisam** a utilizadora; nunca alteram nem bloqueiam valores.
 */

/** Valida um NIF/NIPC português pelo dígito de controlo (módulo 11). */
export function isValidNif(value: string): boolean {
  const digits = value.replace(/\s/g, "");
  if (!/^\d{9}$/.test(digits)) {
    return false;
  }
  let sum = 0;
  for (let i = 0; i < 8; i++) {
    sum += Number(digits[i]) * (9 - i);
  }
  const remainder = sum % 11;
  const check = remainder < 2 ? 0 : 11 - remainder;
  return check === Number(digits[8]);
}
