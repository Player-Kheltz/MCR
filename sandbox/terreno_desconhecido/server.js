"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
require("dotenv/config");
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const helmet_1 = __importDefault(require("helmet"));
const auth_1 = require("./routes/auth");
const products_1 = require("./routes/products");
const posts_1 = require("./routes/posts");
const categories_1 = require("./routes/categories");
const promotions_1 = require("./routes/promotions");
const customers_1 = require("./routes/customers");
const documents_1 = require("./routes/documents");
const messages_1 = require("./routes/messages");
const errorHandler_1 = require("./middleware/errorHandler");
const app = (0, express_1.default)();
const port = process.env.PORT || 3000;
if (!process.env.JWT_SECRET) {
    console.error('FATAL: JWT_SECRET environment variable is required');
    process.exit(1);
}
app.use((0, helmet_1.default)());
app.use((0, cors_1.default)({ origin: process.env.FRONTEND_URL || 'http://localhost:8081' }));
app.use((_req, res, next) => {
    const original = res.json.bind(res);
    res.json = (body) => {
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        return original(body);
    };
    next();
});
app.use(express_1.default.json({ limit: '10mb' }));
app.use('/uploads', express_1.default.static('uploads'));
app.use('/api/auth', auth_1.authRoutes);
app.use('/api/categories', categories_1.categoryRoutes);
app.use('/api/products', products_1.productRoutes);
app.use('/api/customers', customers_1.customerRoutes);
app.use('/api/messages', messages_1.messageRoutes);
app.use('/api/promotions', promotions_1.promotionRoutes);
app.use('/api/documents', documents_1.documentRoutes);
app.use('/api/posts', posts_1.postRoutes);
app.get('/api/health', (_, res) => {
    res.json({ status: 'ok', version: '1.0.0' });
});
app.use(errorHandler_1.errorHandler);
const server = app.listen(port, () => {
    console.log(`Hub do Lojista backend rodando na porta ${port}`);
});
server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.error(`Porta ${port} ja esta em uso. Use: python server.py stop`);
    }
    else {
        console.error('Erro ao iniciar servidor:', err.message);
    }
    process.exit(1);
});
//# sourceMappingURL=server.js.map