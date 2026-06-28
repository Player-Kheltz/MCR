"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.errorHandler = errorHandler;
function errorHandler(err, _req, res, _next) {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    if (err.message?.startsWith('Apenas ')) {
        return res.status(400).json({ error: err.message });
    }
    console.error('Erro:', err.stack || err.message);
    res.status(500).json({ error: 'Erro interno do servidor' });
}
//# sourceMappingURL=errorHandler.js.map