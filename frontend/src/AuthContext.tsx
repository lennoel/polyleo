import { createContext, useContext, useEffect, useState } from "react";
import { api, apiJSON } from "./api";

export interface Usuario {
  id: number;
  username: string;
  email: string;
  es_admin: boolean;
  fecha_registro: string;
}

interface AuthContexto {
  usuario: Usuario | null;
  cargando: boolean;
  entrar: (u: Usuario) => void;
  salir: () => Promise<void>;
}

const Contexto = createContext<AuthContexto>({
  usuario: null,
  cargando: true,
  entrar: () => {},
  salir: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api("/auth/actual/").then(({ datos }) => {
      if (datos.ok) setUsuario(datos.usuario);
      setCargando(false);
    });
  }, []);

  const salir = async () => {
    await apiJSON("/auth/logout/", "POST");
    setUsuario(null);
  };

  return (
    <Contexto.Provider value={{ usuario, cargando, entrar: setUsuario, salir }}>
      {children}
    </Contexto.Provider>
  );
}

export function useAuth() {
  return useContext(Contexto);
}
