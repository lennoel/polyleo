import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import Inicio from "./paginas/Inicio";
import Individual from "./paginas/Individual";
import Lotes from "./paginas/Lotes";
import VideoAnalisis from "./paginas/VideoAnalisis";
import Historial from "./paginas/Historial";
import Perfil from "./paginas/Perfil";
import Acceso from "./paginas/Acceso";
import "./App.css";

function Layout() {
  const { usuario, salir } = useAuth();
  return (
    <div className="contenedor-app">
      <header className="barra">
        <Link to="/" className="marca">
          🩺 Asistente de Segmentación de Pólipos
        </Link>
        <nav>
          <NavLink to="/individual">Imagen individual</NavLink>
          <NavLink to="/lotes">Análisis por lotes</NavLink>
          <NavLink to="/video">Análisis de video</NavLink>
          <NavLink to="/historial">Historial</NavLink>
        </nav>
        <div className="usuario">
          {usuario ? (
            <>
              <Link to="/perfil">👤 {usuario.username}</Link>
              <button className="link" onClick={salir}>
                Cerrar sesión
              </button>
            </>
          ) : (
            <Link to="/acceso">Iniciar sesión</Link>
          )}
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/individual" element={<Individual />} />
          <Route path="/lotes" element={<Lotes />} />
          <Route path="/video" element={<VideoAnalisis />} />
          <Route path="/historial" element={<Historial />} />
          <Route path="/perfil" element={<Perfil />} />
          <Route path="/acceso" element={<Acceso />} />
        </Routes>
      </main>

      <footer className="pie">
        Herramienta de apoyo visual · Las predicciones no constituyen un
        diagnóstico médico
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    </AuthProvider>
  );
}
