// Cliente HTTP de la API del asistente.
// Si la app corre en Vite (5173) usa el backend en 8000;
// si corre servida por Django usa el mismo origen.
export const API =
  window.location.port === "5173" ? "http://localhost:8000" : "";

interface RespuestaAPI {
  estado: number;
  // La forma de "datos" depende del endpoint consultado
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  datos: any;
}

export async function api(
  ruta: string,
  opciones: RequestInit = {},
): Promise<RespuestaAPI> {
  const resp = await fetch(`${API}/api${ruta}`, {
    credentials: "include",
    ...opciones,
  });
  const datos = await resp
    .json()
    .catch(() => ({ ok: false, error: "Respuesta inválida" }));
  return { estado: resp.status, datos };
}

export function apiJSON(ruta: string, metodo: string, cuerpo?: unknown) {
  return api(ruta, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
}

export function apiForm(ruta: string, form: FormData, metodo = "POST") {
  return api(ruta, { method: metodo, body: form });
}

export function urlDescarga(ruta: string) {
  return `${API}${ruta}`;
}
