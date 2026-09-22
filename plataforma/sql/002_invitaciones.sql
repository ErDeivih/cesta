-- Invitar por enlace, no por escribir el nombre de usuario de nadie.
--
-- Pedirle a alguien que teclee "@davidpeve01" para unirse a una lista es pedirle
-- que se equivoque. Un enlace se manda por WhatsApp y se pulsa.
--
-- El enlace caduca y se puede revocar, porque un enlace que dura para siempre
-- acaba reenviado en un grupo que no era.

CREATE TABLE IF NOT EXISTS invitacion (
    codigo      text PRIMARY KEY,           -- va en la URL; se genera aleatorio
    lista_id    uuid NOT NULL REFERENCES lista(id) ON DELETE CASCADE,
    creada_por  uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    papel       text NOT NULL DEFAULT 'escribe' CHECK (papel IN ('escribe', 'mira')),
    usos_max    integer NOT NULL DEFAULT 1 CHECK (usos_max > 0),
    usos        integer NOT NULL DEFAULT 0,
    creada_en   timestamptz NOT NULL DEFAULT now(),
    expira_en   timestamptz NOT NULL,
    revocada_en timestamptz
);
CREATE INDEX IF NOT EXISTS invitacion_por_lista ON invitacion(lista_id);

-- Cuando alguien abrio por ultima vez cada lista. Sirve para "esto es nuevo
-- desde que la miraste", que es lo que hace util una lista compartida: si no,
-- las cosas aparecen y desaparecen sin que sepas quien ni cuando.
CREATE TABLE IF NOT EXISTS visita (
    lista_id   uuid NOT NULL REFERENCES lista(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    vista_en   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (lista_id, usuario_id)
);

-- En el pasillo hay dos estados, no uno: lo que falta por coger y lo que ya
-- llevas en el carro. Tachar sirve para lo segundo; lo que se necesita es poder
-- separar las dos mitades de un vistazo con una mano ocupada.
ALTER TABLE lista_linea ADD COLUMN IF NOT EXISTS en_carrito boolean NOT NULL DEFAULT false;
