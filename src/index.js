const express = require('express');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const app = express();
app.use(express.json());

const SECRET_KEY = process.env.SECRET_KEY;
const LOG_FILE = path.join(__dirname, 'history.txt');

function writeToLog(action, originalText, result) {
  const timestamp = new Date().toISOString();
  const logLine = `[${timestamp}] Ação: ${action} | Original: ${originalText} | Resultado: ${JSON.stringify(result)}\n`;
  fs.appendFile(LOG_FILE, logLine, 'utf8', (err) => {
    if (err) console.error('Erro ao salvar log:', err);
  });
}

function encrypt(text, key) {
  if (!key || key.length !== 32) throw new Error('Chave secreta inválida ou não configurada no arquivo .env');
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-cbc', Buffer.from(key, 'utf-8'), iv);
  let encrypted = cipher.update(text);
  encrypted = Buffer.concat([encrypted, cipher.final()]);
  return { iv: iv.toString('hex'), encryptedData: encrypted.toString('hex') };
}

function decrypt(encryptedObj, key) {
  if (!key || key.length !== 32) throw new Error('Chave secreta inválida ou não configurada no arquivo .env');
  const iv = Buffer.from(encryptedObj.iv, 'hex');
  const encryptedText = Buffer.from(encryptedObj.encryptedData, 'hex');
  const decipher = crypto.createCipheriv('aes-256-cbc', Buffer.from(key, 'utf-8'), iv);
  let decrypted = decipher.update(encryptedText);
  decrypted = Buffer.concat([decrypted, decipher.final()]);
  return decrypted.toString();
}

app.post('/encrypt', (req, res) => {
  const { text } = req.body;
  if (!text) return res.status(400).send('Por favor, envie o campo text.');
  try {
    const encryptedText = encrypt(text, SECRET_KEY);
    writeToLog('CRIPTOGRAFIA', text, encryptedText);
    res.json(encryptedText);
  } catch (error) {
    res.status(500).send(error.message);
  }
});

app.post('/decrypt', (req, res) => {
  const { iv, encryptedData } = req.body;
  if (!iv || !encryptedData) return res.status(400).send('Campos iv e encryptedData são obrigatórios.');
  try {
    const decryptedText = decrypt({ iv, encryptedData }, SECRET_KEY);
    res.send(decryptedText);
  } catch (error) {
    res.status(500).send(error.message);
  }
});

app.get('/count-words', (req, res) => {
  const filePath = path.join(__dirname, 'example.txt');
  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) return res.status(500).json({ error: 'Erro ao ler o arquivo de teste.' });
    const wordCount = data.split(/\s+/).filter(Boolean).length;
    res.json({ wordCount });
  });
});

app.get('/logs', (req, res) => {
  fs.readFile(LOG_FILE, 'utf8', (err, data) => {
    if (err) {
      if (err.code === 'ENOENT') return res.json({ logs: [] });
      return res.status(500).json({ error: 'Erro ao ler histórico.' });
    }
    const lines = data.split('\n').filter(Boolean);
    res.json({ logs: lines });
  });
});

app.get('/status', (req, res) => {
  const uptimeSeconds = process.uptime();
  res.json({
    status: 'online',
    version: '1.1.0',
    uptime: `${Math.floor(uptimeSeconds)} segundos`,
    environment: 'desenvolvimento_local'
  });
});

app.listen(3000, () => {
  console.log('Servidor rodando com segurança (.env) em http://localhost:3000');
});
