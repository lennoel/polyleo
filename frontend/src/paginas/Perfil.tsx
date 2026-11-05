import { useEffect, useState } from "react";
import { api, apiJSON } from "../api";
import { useAuth } from "../AuthContext";
import { Link } from "react-router-dom";

interface UsuarioAdmin {
  id: number;
  username: string;
  email: string;
  es_admin: boolean;
  activo: boolean;
  fecha_registro: string;
}

export default function Perfil() {
  const { usuario, salir } = useAuth();
  const [usuarios, setUsuarios] = useState<UsuarioAdmin[]>([]);

  const cargarUsuarios = async () => {
    const { datos } = await api("/auth/usuarios/");
    if (datos.ok) setUsuarios(datos.usuarios);
  };

  useEffect(() => {
    if (usuario?.es_admin) cargarUsuarios();
  }, [usuario]);

  if (!usuario) {
    return (
      <section className="panel angosto">
        <h2>Mi perfil</h2>
        <p>
          Debes <Link to="/acceso">iniciar sesión</Link> para ver tu perfil.
        </p>
      </section>
    );
  }

  const cambiarEstado = async (id: number) => {
    await apiJSON(`/auth/usuarios/${id}/estado/`, "POST");
    cargarUsuarios();
  };

  return (
    <div>
      <section className="panel angosto">
        <h2>Mi perfil</h2>
        <p>
          <strong>Usuario:</strong> {usuario.username}
        </p>
        <p>
          <strong>Correo:</strong> {usuario.email}
        </p>
        <p>
          <strong>Rol:</strong> {usuario.es_admin ? "Administrador" : "Usuario registrado"}
        </p>
        <p>
          <strong>Registro:</strong>{" "}
          {new Date(usuario.fecha_registro).toLocaleDateString()}
        </p>
        <button onClick={salir}>Cerrar sesión</button>
      </section>

      {usuario.es_admin && (
        <section className="panel">
          <h3>Administración de cuentas</h3>
          <table className="tabla">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{u.email}</td>
                  <td>{u.es_admin ? "Administrador" : "Usuario"}</td>
                  <td>{u.activo ? "Activo" : "Deshabilitado"}</td>
                  <td>
                    {u.id !== usuario.id && (
                      <button className="link" onClick={() => cambiarEstado(u.id)}>
                        {u.activo ? "Deshabilitar" : "Habilitar"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
