import { useRef, useState } from "react";
import { api, apiForm, urlDescarga } from "../api";
import { useAuth } from "../AuthContext";
import { Link } from "react-router-dom";

interface EstadoVideo {
  id: number;
  estado: string;
  progreso: number;
  tiempo_procesamiento: number;
  detalle: {
    duracion_seg?: number;
    fps_original?: number;
    total_frames?: number;
    frames_analizados?: number;
    intervalos?: [number, number][];
    video_url?: string;
    original_url?: string;
    error?: string;
  };
}

export default function VideoAnalisis() {
  const { usuario } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [vistaPrevia, setVistaPrevia] = useState<string | null>(null);
  const [subiendo, setSubiendo] = useState(false);
  const [estado, setEstado] = useState<EstadoVideo | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!usuario) {
    return (
      <section className="panel angosto">
        <h2>Análisis de video</h2>
        <p>
          Debes <Link to="/acceso">iniciar sesión</Link> para usar esta
          funcionalidad.
        </p>
      </section>
    );
  }

  const seleccionar = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setArchivo(f);
    setEstado(null);
    setError(null);
    setVistaPrevia(f ? URL.createObjectURL(f) : null);
  };

  const procesar = async () => {
    if (!archivo) return;
    setSubiendo(true);
    setError(null);
    const form = new FormData();
    form.append("video", archivo);
    const { datos } = await apiForm("/videos/", form);
    setSubiendo(false);
    if (!datos.ok) {
      setError(datos.error ?? "Error al subir el video");
      return;
    }
    consultarEstado(datos.id);
  };

  const consultarEstado = (id: number) => {
    const intervalo = window.setInterval(async () => {
      const { datos } = await api(`/videos/${id}/estado/`);
      if (datos.ok) {
        setEstado(datos as EstadoVideo);
        if (datos.estado !== "procesando") {
          window.clearInterval(intervalo);
        }
      } else {
        window.clearInterval(intervalo);
        setError("No se pudo consultar el estado");
      }
    }, 2000);
  };

  const detalle = estado?.detalle;
  const duracion = detalle?.duracion_seg ?? 0;

  return (
    <div>
      <section className="panel">
        <h2>Análisis de video de colonoscopia</h2>
        <p className="nota">
          Formato MP4 · máx. 200 MB y 2 minutos · se analizan 2 fotogramas
          por segundo (los demás se copian sin modificar).
        </p>
        <div className="acciones">
          <button onClick={() => inputRef.current?.click()}>
            Seleccionar video
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".mp4"
            hidden
            onChange={seleccionar}
          />
          <button className="primario" disabled={!archivo || subiendo} onClick={procesar}>
            {subiendo ? "Subiendo…" : "Analizar video"}
          </button>
        </div>
        {vistaPrevia && (
          <div className="vista-previa">
            <video src={vistaPrevia} controls width={480} />
          </div>
        )}
        {error && <p className="error">⚠ {error}</p>}
        {estado && estado.estado === "procesando" && (
          <div className="progreso">
            <div className="progreso-barra" style={{ width: `${estado.progreso}%` }} />
            <span>Procesando… {estado.progreso}%</span>
          </div>
        )}
      </section>

      {estado && estado.estado === "completado" && detalle && (
        <section className="panel">
          <h3>Video segmentado</h3>
          <div className="vista-previa">
            <video src={urlDescarga(detalle.video_url!)} controls width={640} />
          </div>
          <div className="stats">
            <span>
              Duración: <strong>{detalle.duracion_seg}s</strong>
            </span>
            <span>
              Fotogramas: <strong>{detalle.frames_analizados} / {detalle.total_frames}</strong>
            </span>
            <span>
              Tiempo total:{" "}
              <strong>{(estado.tiempo_procesamiento / 1000).toFixed(1)}s</strong>
            </span>
          </div>

          <h4>Línea de tiempo de regiones segmentadas</h4>
          <div className="timeline">
            {detalle.intervalos?.map(([ini, fin], i) => (
              <div
                key={i}
                className="segmento"
                style={{
                  left: `${(ini / duracion) * 100}%`,
                  width: `${Math.max(((fin - ini) / duracion) * 100, 1)}%`,
                }}
                title={`${ini}s – ${fin}s`}
              />
            ))}
          </div>
          <p className="nota">
            Intervalos con regiones predichas (rojo). Una región detectada en
            un fotograma no garantiza que sea un pólipo real.
          </p>
          <a className="boton primario" href={urlDescarga(detalle.video_url!)} download="video_segmentado.mp4">
            Descargar video procesado
          </a>
        </section>
      )}
      {estado && estado.estado === "error" && (
        <p className="error">⚠ {detalle?.error ?? "Error en el procesamiento"}</p>
      )}
    </div>
  );
}
