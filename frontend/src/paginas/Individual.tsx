import { useRef, useState } from "react";
import { apiForm, urlDescarga } from "../api";

interface Resultado {
  id: number;
  analisis_id: number;
  area_segmentada: number;
  tiempo_inferencia_ms: number;
  estado: string;
  error: string;
  original_url: string;
  mascara_url: string;
  overlay_url: string;
  calor_url: string;
  informe_url: string;
}

export default function Individual() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [vistaPrevia, setVistaPrevia] = useState<string | null>(null);
  const [umbral, setUmbral] = useState(0.5);
  const [transparencia, setTransparencia] = useState(0.5);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const seleccionar = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setArchivo(f);
    setResultado(null);
    setError(null);
    setVistaPrevia(f ? URL.createObjectURL(f) : null);
  };

  const analizar = async () => {
    if (!archivo) return;
    setCargando(true);
    setError(null);
    const form = new FormData();
    form.append("imagen", archivo);
    form.append("umbral", String(umbral));
    form.append("transparencia", String(transparencia));
    const { datos } = await apiForm("/segmentar/", form);
    setCargando(false);
    if (datos.ok) setResultado(datos as Resultado);
    else setError(datos.error ?? "Error en el análisis");
  };

  const nuevo = () => {
    setArchivo(null);
    setVistaPrevia(null);
    setResultado(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div>
      <section className="panel">
        <h2>Análisis de imagen individual</h2>
        <div className="acciones">
          <button onClick={() => inputRef.current?.click()}>
            Seleccionar imagen
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png"
            hidden
            onChange={seleccionar}
          />
          <button className="primario" disabled={!archivo || cargando} onClick={analizar}>
            {cargando ? "Analizando…" : "Analizar"}
          </button>
          <button onClick={nuevo}>Nuevo análisis</button>
        </div>

        <div className="controles">
          <label>
            Umbral de detección: <strong>{umbral.toFixed(2)}</strong>
            <input
              type="range"
              min={0.1}
              max={0.9}
              step={0.05}
              value={umbral}
              onChange={(e) => setUmbral(Number(e.target.value))}
            />
          </label>
          <label>
            Transparencia de la máscara: <strong>{Math.round(transparencia * 100)}%</strong>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={transparencia}
              onChange={(e) => setTransparencia(Number(e.target.value))}
            />
          </label>
        </div>

        {vistaPrevia && (
          <div className="vista-previa">
            <img src={vistaPrevia} alt="Colonoscopia seleccionada" />
          </div>
        )}
        {error && <p className="error">⚠ {error}</p>}
      </section>

      {resultado && (
        <section className="panel">
          <h3>Resultado</h3>
          {resultado.estado === "sin_regiones" && (
            <p className="aviso">
              No se identificaron regiones segmentadas con el umbral actual.
            </p>
          )}
          <div className="rejilla">
            <figure>
              <img src={urlDescarga(resultado.original_url)} alt="Original" />
              <figcaption>Imagen original</figcaption>
            </figure>
            <figure>
              <img src={urlDescarga(resultado.mascara_url)} alt="Máscara" />
              <figcaption>Máscara predicha</figcaption>
            </figure>
            <figure>
              <img src={urlDescarga(resultado.overlay_url)} alt="Superposición" />
              <figcaption>Segmentación superpuesta</figcaption>
            </figure>
            <figure>
              <img src={urlDescarga(resultado.calor_url)} alt="Mapa de calor" />
              <figcaption>Mapa de probabilidad</figcaption>
            </figure>
          </div>
          <div className="stats">
            <span>
              Área segmentada: <strong>{resultado.area_segmentada}%</strong>
            </span>
            <span>
              Tiempo de inferencia:{" "}
              <strong>{resultado.tiempo_inferencia_ms} ms</strong>
            </span>
          </div>
          <div className="acciones">
            <a className="boton" href={urlDescarga(resultado.mascara_url)} download="mascara.png">
              Descargar máscara
            </a>
            <a className="boton" href={urlDescarga(resultado.overlay_url)} download="superposicion.png">
              Descargar superposición
            </a>
            <a className="boton primario" href={urlDescarga(resultado.informe_url)}>
              Descargar informe PDF
            </a>
          </div>
          <p className="nota">
            Predicción visual del modelo; no constituye un diagnóstico médico.
          </p>
        </section>
      )}
    </div>
  );
}
