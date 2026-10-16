/** Session actions require server confirmation; cached profiles never authorize. */
export async function verifyReviewerSession(token) {
  if (!token) throw new Error('Sesion requerida.');
  const response = await fetch('/api/auth/session', {
    headers: { Authorization: `Bearer ${token}` }, cache: 'no-store'
  });
  const result = typeof response.json === 'function' ? await response.json() : {};
  if (!response.ok || result.valid !== true || !result.veedor || !result.expiresAt) {
    const failure = new Error(result.error || 'No se pudo verificar la acreditacion.');
    failure.reason = response.status >= 500 ? 'error' : 'expired';
    throw failure;
  }
  return result.veedor;
}

export async function closeReviewerSession(token) {
  const response = await fetch('/api/auth/logout', {
    method: 'POST', headers: { Authorization: `Bearer ${token}` }, cache: 'no-store'
  });
  if (!response.ok) throw new Error('No se pudo confirmar el cierre de sesion.');
  sessionStorage.removeItem('cajamarca_veedor_token');
  sessionStorage.removeItem('cajamarca_veedor_profile');
}
