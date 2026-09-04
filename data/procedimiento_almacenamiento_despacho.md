# Procedimiento operativo — Almacenamiento y despacho de producto terminado (PO-LOG-07)

## 1. Objetivo y alcance
Establecer la secuencia de actividades para recibir, almacenar y despachar producto terminado desde el
depósito central, garantizando la trazabilidad de cada pallet y la exactitud del inventario en SAP.
Aplica al personal de depósito, operadores de autoelevador y al analista de logística.

## 2. Recepción desde producción
1. Cada pallet que ingresa desde producción debe tener una etiqueta con código de barras que identifica
   número de lote, fecha de producción y cantidad de unidades.
2. El operador escanea la etiqueta con el lector de mano. El sistema WMS registra el ingreso y asigna
   una ubicación (pasillo-columna-nivel, por ejemplo B-12-3).
3. Si la etiqueta no se puede leer, el pallet se coloca en la zona de cuarentena Q-01 y se avisa al
   supervisor. No se puede ubicar un pallet sin lectura válida.

## 3. Almacenamiento
- El depósito usa el criterio FEFO (First Expired, First Out): sale primero el lote con vencimiento más próximo.
- Los pallets se almacenan en racks selectivos de 3 niveles. El nivel 3 se reserva para lotes con más de
  90 días hasta el vencimiento.
- La altura máxima de apilado en piso es de 2 pallets, y solo para productos marcados como apilables.
- La temperatura del depósito debe mantenerse entre 15 °C y 25 °C. Se registra dos veces por turno.
- Está prohibido almacenar producto terminado en los pasillos de circulación o frente a las salidas de emergencia.

## 4. Preparación de pedidos (picking)
1. El analista de logística libera las órdenes de despacho en SAP antes de las 10:00 hs para los
   despachos del mismo día.
2. El WMS genera la lista de picking respetando FEFO y la envía al lector del operador.
3. El operador retira los pallets indicados, escanea cada uno al retirarlo y los lleva a la zona de
   preparación P-02.
4. Toda diferencia entre la cantidad física y la cantidad del sistema se reporta en el momento; no se
   corrige manualmente en SAP sin autorización del supervisor.

## 5. Despacho
1. Antes de cargar, se verifica el remito contra la lista de picking: cliente, cantidad, lote.
2. El pesaje del camión se realiza en la balanza de salida. El peso neto se registra en el remito y en SAP.
   Una diferencia mayor al 2 % entre el peso teórico y el pesado bloquea el despacho hasta revisión.
3. El transportista firma el remito por triplicado: original para el cliente, duplicado para logística,
   triplicado para el transportista.
4. El horario de despacho es de lunes a viernes de 8:00 a 17:00 hs. Fuera de ese horario se requiere
   autorización del jefe de logística.

## 6. Inventario cíclico
Cada semana se cuenta el 10 % de las ubicaciones, priorizando las de mayor rotación. Las diferencias se
investigan antes de ajustar. Un desvío de inventario superior al 0,5 % del stock total dispara un
recuento general.
