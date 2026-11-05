import { Link } from "react-router-dom";

const opciones = [
  { ruta: "/individual", icono: "🖼️", titulo: "Imagen individual", texto: "Analizar una imagen" },
  { ruta: "/lotes", icono: "🗂️", titulo: "Análisis por lotes", texto: "Procesar varias imágenes" },
  { ruta: "/video", icono: "🎞️", titulo: "Análisis de video", texto: "Procesar fotogramas" },
  { ruta: "/historial", icono: "🕘", titulo: "Historial", texto: "Consultar resultados" },
  { ruta: "/perfil", icono: "👤", titulo: "Mi perfil", texto: "Administrar la cuenta" },
];

export default function Inicio() {
  return (
    <div>
      <section className="panel">
        <h1>Asistente Inteligente de Segmentación de Pólipos</h1>
        <p className="subtitulo">
          Detección y segmentación en imágenes de colonoscopia mediante
          Vision Transformers (ViT) · Aplicación web local
        </p>
        <p>
          El sistema analiza imágenes y videos de colonoscopia y resalta las
          regiones que el modelo predice como pólipos, como apoyo a la
          revisión del especialista.
        </p>
      </section>

      <div className="tarjetas">
        {opciones.map((o) => (
          <Link key={o.ruta} to={o.ruta} className="tarjeta">
            <span className="icono">{o.icono}</span>
            <strong>{o.titulo}</strong>
            <span>{o.texto}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
