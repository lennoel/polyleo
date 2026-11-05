import { useEffect, useState } from "react";
import { api, urlDescarga } from "../api";
import { useAuth } from "../AuthContext";
import { Link } from "react-router-dom";

interface Analisis {
  id: number;
  tipo: string;
  fecha: string;
  estado: string;
  detalle: Record<string, unknown>;
}

interface ResultadoDetalle {
  id: number;
  nombre_archivo: string;
  area_segmentada: number;
  tiempo_inferencia_ms: number;
  estado: string;
  original_url: string | null;
  mascara_url: string | null;
  overlay_url: string | null;
  calor_url: string | null;
  informe_url: string;
}

export default function Historial() {
  const { usuario } = useAuth();
  const [registros, setRegistros] = useState<Analisis[]>([]);
  const [texto, setTexto] = useState("");
  const [tipo, setTipo] = useState("");
  const [detalle, setDetalle] = useState<(Analisis & { resultados?: ResultadoDetalle[] }) | null>(null);

  const cargar = async () => {
    const { datos } = await api(`/historial/?q=${encodeURIComponent(texto)}&tipo=${tipo}`);
    if (datos.ok) setRegistros(datos.analisis);
  };

  useEffect(() => {
    if (usuario) cargar();
  }, [usuario]);

  if (!usuario) {
    return (
      <section className="panel angosto">
        <h2>Historial de análisis</h2>
        <p>
          Debes <Link to="/acceso">iniciar sesión</Link> para consultar tu
          historial.
        </p>
      </section>
    );
  }

  const verDetalle = async (id: number) => {
    const { datos } = await api(`/analisis/${id}/`);
    if (datos.ok) setDetalle(datos);
  };

  const eliminar = async (id: number) => {
    if (!window.confirm("¿Eliminar este análisis y sus resultados?")) return;
    await api(`/analisis/${id}/`, { method: "DELETE" });
    setDetalle(null);
    cargar();
  };

  return (
    <div>
      <section className="panel">
        <h2>Historial de análisis</h2>
        <div className="filtros">
          <input
            placeholder="Buscar por nombre de archivo…"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
          />
          <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="">Todos los tipos</option>
            <option value="imagen">Imagen</option>
            <option value="lote">Lote</option>
            <option value="video">Video</option>
          </select>
          <button onClick={cargar}>Buscar</button>
        </div>
        <table className="tabla">
          <thead>
            <tr>
              <th>ID</th>
              <th>Fecha</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {registros.map((r) => (
              <tr key={r.id}>
                <td>#{r.id}</td>
                <td>{new Date(r.fecha).toLocaleString()}</td>
                <td>{r.tipo}</td>
                <td>{r.estado}</td>
                <td>
                  <button className="link" onClick={() => verDetalle(r.id)}>
                    Ver resultado
                  </button>
                  {" · "}
                  <button className="link peligro" onClick={() => eliminar(r.id)}>
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
            {!registros.length && (
              <tr>
                <td colSpan={5}>No hay análisis registrados.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {detalle && (
        <section className="panel">
          <h3>
            Análisis #{detalle.id} ({detalle.tipo})
          </h3>
          {detalle.tipo === "video" && detalle.detalle?.video_url ? (
            <div>
              <video src={urlDescarga(detalle.detalle.video_url as string)} controls width={560} />
              <p>
                <a href={urlDescarga(detalle.detalle.video_url as string)} download>
                  Descargar video segmentado
                </a>
              </p>
            </div>
          ) : (
            <div className="rejilla">
              {detalle.resultados?.map((r) =>
                r.overlay_url ? (
                  <figure key={r.id}>
                    <img src={urlDescarga(r.overlay_url)} alt={r.nombre_archivo} />
                    <figcaption>
                      {r.nombre_archivo} · {r.area_segmentada}% ·{" "}
                      <a href={urlDescarga(r.informe_url)}>Informe PDF</a>
                    </figcaption>
                  </figure>
                ) : null,
              )}
            </div>
          )}
          {detalle.tipo === "lote" && (
            <div className="acciones">
              <a className="boton" href={urlDescarga(`/api/lotes/${detalle.id}/descargar.zip`)}>
                Descargar ZIP
              </a>
              <a className="boton" href={urlDescarga(`/api/lotes/${detalle.id}/exportar.csv`)}>
                Exportar CSV
              </a>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
