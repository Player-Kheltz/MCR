const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();
p.user.findMany()
  .then(u => console.log(JSON.stringify(u)))
  .catch(e => console.error('Error:', e.message, e.stack))
  .finally(() => p.$disconnect());
