"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AuthController = void 0;
const bcryptjs_1 = __importDefault(require("bcryptjs"));
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const prisma_1 = require("../lib/prisma");
const zod_1 = require("zod");
const registerSchema = zod_1.z.object({
    storeName: zod_1.z.string().min(2),
    cnpj: zod_1.z.string().min(14).max(18),
    phone: zod_1.z.string().min(8),
    address: zod_1.z.string().min(5),
    name: zod_1.z.string().min(2),
    email: zod_1.z.string().email(),
    password: zod_1.z.string().min(6),
});
const loginSchema = zod_1.z.object({
    email: zod_1.z.string().email(),
    password: zod_1.z.string().min(1),
});
class AuthController {
    async register(req, res) {
        try {
            const data = registerSchema.parse(req.body);
            const existingUser = await prisma_1.prisma.user.findUnique({ where: { email: data.email } });
            if (existingUser) {
                return res.status(400).json({ error: 'Email já cadastrado' });
            }
            const hashedPassword = await bcryptjs_1.default.hash(data.password, 10);
            const store = await prisma_1.prisma.store.create({
                data: {
                    name: data.storeName,
                    cnpj: data.cnpj,
                    phone: data.phone,
                    address: data.address,
                    users: {
                        create: {
                            name: data.name,
                            email: data.email,
                            password: hashedPassword,
                            role: 'admin',
                        },
                    },
                },
                include: { users: true },
            });
            const user = store.users[0];
            const token = jsonwebtoken_1.default.sign({ userId: user.id, storeId: store.id }, process.env.JWT_SECRET, { expiresIn: '7d' });
            return res.status(201).json({
                token,
                user: { id: user.id, name: user.name, email: user.email, role: user.role },
                store: { id: store.id, name: store.name },
            });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao registrar' });
        }
    }
    async login(req, res) {
        try {
            const data = loginSchema.parse(req.body);
            const user = await prisma_1.prisma.user.findUnique({
                where: { email: data.email },
                include: { store: true },
            });
            if (!user) {
                return res.status(401).json({ error: 'Email ou senha incorretos' });
            }
            const validPassword = await bcryptjs_1.default.compare(data.password, user.password);
            if (!validPassword) {
                return res.status(401).json({ error: 'Email ou senha incorretos' });
            }
            const token = jsonwebtoken_1.default.sign({ userId: user.id, storeId: user.storeId }, process.env.JWT_SECRET, { expiresIn: '7d' });
            return res.json({
                token,
                user: { id: user.id, name: user.name, email: user.email, role: user.role },
                store: { id: user.store.id, name: user.store.name },
            });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao fazer login' });
        }
    }
    async me(req, res) {
        try {
            const userId = req.userId;
            const user = await prisma_1.prisma.user.findUnique({
                where: { id: userId },
                select: {
                    id: true, name: true, email: true, role: true,
                    store: { select: { id: true, name: true } },
                },
            });
            if (!user) {
                return res.status(404).json({ error: 'Usuário não encontrado' });
            }
            return res.json(user);
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao buscar usuário' });
        }
    }
}
exports.AuthController = AuthController;
//# sourceMappingURL=AuthController.js.map