function doPost(e) {
  var ss = SpreadsheetApp.openByUrl("https://docs.google.com/spreadsheets/d/1A7FZqt8mxxrV8fLPYWVdrKV3HcWAZZvQeMpdKWfDmSE/edit");
  var sheet = ss.getSheetByName("REGISTROS");
  var data = JSON.parse(e.postData.contents);
  
  // ORDEN EXACTO PARA 14 COLUMNAS (A-N)
  sheet.appendRow([
    data.Fecha,      // A
    data.Cedula,     // B
    data.Mensajero,  // C
    data.Empresa,    // D
    data.Ciudad,     // E
    data.Producto,   // F
    data.Tienda_O,   // G (Tienda Origen)
    data.Cod_O,      // H (Cod_Rec)
    "",              // I (Columna vacía según tu imagen)
    data.Cod_D,      // J (Cod_Ent)
    data.Tienda_D,   // K (Tienda Destino)
    data.Cant,       // L
    data.Inicio,     // M
    data.Llegada,    // N
    data.Minutos     // O
  ]);
  
  return ContentService.createTextOutput("Éxito");
}
