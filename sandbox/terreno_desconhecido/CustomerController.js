"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CustomerController = void 0;
const prisma_1 = require("../lib/prisma");
const zod_1 = require("zod");
const optimizer_1 = require("../lib/optimizer");
const safeJson_1 = require("../lib/safeJson");
const customerSchema = zod_1.z.object({
    name: zod_1.z.string().min(1).transform(v => optimizer_1.Optimizer.normalizeName(v)),
    phone: zod_1.z.string().optional().transform(v => v ? optimizer_1.Optimizer.normalizePhone(v) : undefined),
    email: zod_1.z.string().trim().email().optional().or(zod_1.z.literal('')).transform(v => v ? optimizer_1.Optimizer.normalizeEmail(v) : undefined),
    cpf: zod_1.z.string().optional().transform(v => v ? optimizer_1.Optimizer.normalizeDocument(v) : undefined),
    address: zod_1.z.string().optional().transform(v => v?.trim() || undefined),
    notes: zod_1.z.string().optional().transform(v => v?.trim() || undefined),
    source: zod_1.z.string().optional().transform(v => v?.trim() || undefined),
});
class CustomerController {
    async list(req, res) {
        try {
            const customers = await prisma_1.prisma.customer.findMany({
                where: { storeId: req.storeId },
                orderBy: { createdAt: 'desc' },
            });
            return res.json(customers);
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao listar clientes' });
        }
    }
    async getById(req, res) {
        try {
            const customer = await prisma_1.prisma.customer.findFirst({
                where: { id: req.params.id, storeId: req.storeId },
                include: {
                    documents: {
                        orderBy: { createdAt: 'desc' },
                        select: { id: true, templateId: true, category: true, data: true, status: true, createdAt: true },
                    },
                },
            });
            if (!customer)
                return res.status(404).json({ error: 'Cliente não encontrado' });
            return res.json({
                ...customer,
                documents: customer.documents.map(d => ({ ...d, data: (0, safeJson_1.safeJsonParse)(d.data, {}) })),
            });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao buscar cliente' });
        }
    }
    async create(req, res) {
        try {
            const data = customerSchema.parse(req.body);
            const customer = await prisma_1.prisma.customer.create({
                data: {
                    storeId: req.storeId,
                    name: data.name,
                    phone: data.phone ?? null,
                    email: data.email ?? null,
                    cpf: data.cpf ?? null,
                    address: data.address ?? null,
                    notes: data.notes ?? null,
                    source: data.source ?? null,
                },
            });
            return res.status(201).json(customer);
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao criar cliente' });
        }
    }
    async update(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.customer.findFirst({ where: { id, storeId } });
            if (!existing)
                return res.status(404).json({ error: 'Cliente não encontrado' });
            const data = customerSchema.partial().parse(req.body);
            const customer = await prisma_1.prisma.customer.update({ where: { id }, data });
            return res.json(customer);
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao atualizar cliente' });
        }
    }
    async delete(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.customer.findFirst({ where: { id, storeId } });
            if (!existing)
                return res.status(404).json({ error: 'Cliente não encontrado' });
            await prisma_1.prisma.customer.delete({ where: { id } });
            return res.json({ message: 'Cliente removido' });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao remover cliente' });
        }
    }
}
exports.CustomerController = CustomerController;
//# sourceMappingURL=CustomerController.js.map