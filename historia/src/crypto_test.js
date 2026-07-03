const crypto = require('crypto');

function encrypt(text, key) {
  const iv = crypto.randomBytes(16);
  // Garante que a chave passada seja convertida em um Buffer
  const cipher = crypto.createCipheriv('aes-256-cbc', Buffer.from(key, 'utf-8'), iv);
  let encrypted = cipher.update(text);
  encrypted = Buffer.concat([encrypted, cipher.final()]);
  return { iv: iv.toString('hex'), encryptedData: encrypted.toString('hex') };
}

function decrypt(text, key) {
  const iv = Buffer.from(text.iv, 'hex');
  const encryptedText = Buffer.from(text.encryptedData, 'hex');
  const decipher = crypto.createDecipheriv('aes-256-cbc', Buffer.from(key, 'utf-8'), iv);
  let decrypted = decipher.update(encryptedText);
  decrypted = Buffer.concat([decrypted, decipher.final()]);
  return decrypted.toString();
}

// Chave com EXATAMENTE 32 caracteres (32 bytes) para o AES-256
const secretKey = 'abcdefghijklmnopqrstuvwxyz123456'; 
const textToHide = "Texto super secreto do Projeto MCR";

// Execução do teste
const encrypted = encrypt(textToHide, secretKey);
console.log('Texto Criptografado:', encrypted);

const decrypted = decrypt(encrypted, secretKey);
console.log('Texto Descriptografado:', decrypted);
