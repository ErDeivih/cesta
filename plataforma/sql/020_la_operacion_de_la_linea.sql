-- *** La operacion de la que viene cada linea de la lista. *** *
--
-- **Por que existe.** *El 14/10/2026 el propietario decidio que **la lista acumula**: *dos operaciones
-- distintas sobre el mismo ingrediente **se suman**, *y **la misma operacion repetida no duplica.** *
--
-- *Y eso no se podia hacer con el `id` de la linea, *que ya es `id_de_linea(lista_id, clave|operacion)`: *
-- *** `uuid5` es un HASH ***, *asi que de `id_de_linea(lista_id, 'tomate|2026-11-02|2026-11-08')`
-- **no se puede recuperar la operacion.** *
--
-- *Y **por eso el traspaso la tiene en columnas** *(-- `receta_id`, `version`, `semana` --)*: *
-- *un id sirve para que **dos cosas iguales den el mismo** *y **dos distintas den otro**, *y nada mas.* *
--
-- **`NULL` quiere decir «no viene de una operacion»** *-- *una linea escrita a mano, por ejemplo.* *
-- *Y **no se rellena hacia atras** a proposito: *las lineas que ya existen **no se sabe de donde
-- vinieron**, *y **inventarles una operacion** seria decir algo que no consta.* *

ALTER TABLE lista_linea ADD COLUMN IF NOT EXISTS operacion text;

-- *Y el indice, **porque `ya` la consulta en cada pasada del puente**: *
-- *y sin el, traer el plan **recorreria la tabla entera** de la lista, *que crece con el uso.* *
CREATE INDEX IF NOT EXISTS lista_linea_por_operacion ON lista_linea (lista_id, operacion);
