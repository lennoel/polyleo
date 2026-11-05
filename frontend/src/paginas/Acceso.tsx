import { useState } from "react";
import { apiJSON } from "../api";
import { useAuth } from "../AuthContext";
import { useNavigate } from "react-router-dom";

export default function Acceso() {
  const { entrar } = useAuth();
  const navigate = useNavigate();
  const [modo, setModo] = useState<"login" | "registro">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    setCargando(true);
    setError(null);
    const ruta = modo === "login" ? "/auth/login/" : "/auth/registro/";
    const cuerpo =
      modo === "login"
        ? { usuario: email, contrasena: password }
        : { username, email, password };
    const { datos } = await apiJSON(ruta, "POST", cuerpo);
    setCargando(false);
    if (datos.ok) {
      entrar(datos.usuario);
      navigate("/");
    } else {
      setError(datos.error ?? "Error");
    }
  };

  return (
    <section className="panel angosto">
      <h2>{modo === "login" ? "Iniciar sesión" : "Crear cuenta"}</h2>
      <form onSubmit={enviar} className="formulario">
        {modo === "registro" && (
          <label>
            Nombre de usuario
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>
        )}
        <label>
          {modo === "login" ? "Usuario o correo" : "Correo electrónico"}
          <input
            type={modo === "login" ? "text" : "email"}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>
        {error && <p className="error">⚠ {error}</p>}
        <button className="primario" disabled={cargando}>
          {cargando
            ? "Procesando…"
            : modo === "login"
              ? "Iniciar sesión"
              : "Registrarse"}
        </button>
      </form>
      <p className="centrado">
        {modo === "login" ? (
          <>
            ¿No tienes cuenta?{" "}
            <button className="link" onClick={() => setModo("registro")}>
              Regístrate
            </button>
          </>
        ) : (
          <>
            ¿Ya tienes cuenta?{" "}
            <button className="link" onClick={() => setModo("login")}>
              Inicia sesión
            </button>
          </>
        )}
      </p>
    </section>
  );
}
