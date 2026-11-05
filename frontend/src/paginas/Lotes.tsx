import { useRef, useState } from "react";
import { api, apiForm, urlDescarga } from "../api";
import { useAuth } from "../AuthContext";
import { Link } from "react-router-dom";

interface Item {
  archivo: File;
  estado: "pendiente" | "procesando" | "procesada" | "sin_regiones" | "error";
  area?: number;
  tiempo?: number;
  mascara_url?: string;
  overlay_url?: string;
  error?: string;
}

export default function Lotes() {
  const { usuario } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [procesando, setProcesando] = useState(false);
  const [loteId, setLoteId] = useState<number | null>(null);
  const [resumen, setResumen] = useState<{
    total: number;
    con_regiones: number;
    sin_regiones: number;
    errores: number;
  } | null>(null);

  if (!usuario) {
    return (
      <section className="panel angosto">
        <h2>Análisis por lotes</h2>
        <p>
          Debes <Link to="/acceso">iniciar sesión</Link> para usar esta
          funcionalidad.
        </p>
      </section>
    );
  }

  const seleccionar = (e: React.ChangeEvent<HTMLInputElement>) => {
    const archivos = Array.from(e.target.files ?? []).slice(0, 50);
    setItems(archivos.map((archivo) => ({ archivo, estado: "pendiente" })));
    setResumen(null);
    setLoteId(null);
  };

  const procesar = async () => {
    if (!items.length) return;
    setProcesando(true);
    const { datos } = await api("/lotes/", { method: "POST" });
    const id = datos.id as number;
    setLoteId(id);

    const copia = [...items];
    for (let i = 0; i < copia.length; i++) {
      copia[i].estado = "procesando";
      setItems([...copia]);
      const form = new FormData();
      form.append("imagen", copia[i].archivo);
      const { datos: r } = await apiForm(`/lotes/${id}/imagenes/`, form);
      copia[i].estado = r.estado ?? (r.ok ? "procesada" : "error");
      copia[i].area = r.area_segmentada;
      copia[i].tiempo = r.tiempo_inferencia_ms;
      copia[i].mascara_url = r.mascara_url;
      copia[i].overlay_url = r.overlay_url;
      copia[i].error = r.error;
      setItems([...copia]);
    }
    const { datos: fin } = await api(`/lotes/${id}/finalizar/`, { method: "POST" });
    if (fin.ok) setResumen(fin.detalle);
    setProcesando(false);
  };

  const procesadas = items.filter((i) => i.estado !== "pendiente" && i.estado !== "procesando").length;

  return (
    <div>
      <section className="panel">
        <h2>Análisis de imágenes por lotes</h2>
        <div className="acciones">
          <button onClick={() => inputRef.current?.click()}>
            Seleccionar imágenes
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png"
            multiple
            hidden
            onChange={seleccionar}
          />
          <button className="primario" disabled={!items.length || procesando} onClick={procesar}>
            {procesando ? "Procesando…" : "Analizar lote"}
          </button>
        </div>
        {items.length > 0 && (
          <p>
            {items.length} imagen(es) seleccionada(s) (máx. 50)
          </p>
        )}
        {procesando && (
          <div className="progreso">
            <div className="progreso-barra" style={{ width: `${(procesadas / items.length) * 100}%` }} />
            <span>
              {procesadas} / {items.length} procesadas
            </span>
          </div>
        )}
        {items.length > 0 && (
          <table className="tabla">
            <thead>
              <tr>
                <th>Imagen</th>
                <th>Tamaño</th>
                <th>Área segmentada</th>
                <th>Tiempo</th>
                <th>Estado</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={i}>
                  <td>{item.archivo.name}</td>
                  <td>{(item.archivo.size / 1024).toFixed(0)} KB</td>
                  <td>{item.area !== undefined ? `${item.area}%` : "—"}</td>
                  <td>{item.tiempo !== undefined ? `${item.tiempo} ms` : "—"}</td>
                  <td>
                    {item.estado === "sin_regiones"
                      ? "Sin regiones"
                      : item.estado === "error"
                        ? `Error: ${item.error}`
                        : item.estado}
                  </td>
                  <td>
                    {item.overlay_url && (
                      <a href={urlDescarga(item.overlay_url)} target="_blank">
                        Ver
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {resumen && loteId && (
        <section className="panel">
          <h3>Resumen del lote</h3>
          <p>
            {resumen.total} procesadas · {resumen.con_regiones} con regiones
            segmentadas · {resumen.sin_regiones} sin regiones ·{" "}
            {resumen.errores} con error
          </p>
          <div className="acciones">
            <a className="boton primario" href={urlDescarga(`/api/lotes/${loteId}/descargar.zip`)}>
              Descargar ZIP
            </a>
            <a className="boton" href={urlDescarga(`/api/lotes/${loteId}/exportar.csv`)}>
              Exportar CSV
            </a>
          </div>
        </section>
      )}
    </div>
  );
}
