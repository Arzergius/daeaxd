// app.js
const express = require('express');
const path = require('path');
const app = express();
const port = 3001; // Puedes cambiar el puerto si es necesario

// Configuramos Express para servir archivos estáticos desde la carpeta actual
app.use(express.static(path.join(__dirname)));

app.get('/', (req, res) => {
  // Enviamos el archivo node.html como respuesta
  res.sendFile(path.join(__dirname, 'node.html'));
});

app.listen(port, () => {
  console.log(`Servidor de recomendaciones iniciado en http://localhost:${port}`);
});
