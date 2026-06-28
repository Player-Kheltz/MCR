"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PromotionController = void 0;
const prisma_1 = require("../lib/prisma");
const zod_1 = require("zod");
const safeJson_1 = require("../lib/safeJson");
const promotionSchema = zod_1.z.object({
    title: zod_1.z.string().min(1).max(100),
    description: zod_1.z.string().optional(),
    discount: zod_1.z.coerce.number().min(0).max(100).optional(),
    products: zod_1.z.array(zod_1.z.string()).optional(),
    conditions: zod_1.z.string().optional(),
    startDate: zod_1.z.string().optional(),
    endDate: zod_1.z.string().optional(),
    status: zod_1.z.enum(['draft', 'active', 'ended']).optional(),
});
class PromotionController {
    async list(req, res) {
        try {
            const promotions = await prisma_1.prisma.promotion.findMany({
                where: { storeId: req.storeId },
                orderBy: { createdAt: 'desc' },
            });
            return res.json(promotions.map(p => ({ ...p, products: (0, safeJson_1.safeJsonParse)(p.products, []) })));
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao listar promocoes' });
        }
    }
    async active(req, res) {
        try {
            const now = new Date();
            const promos = await prisma_1.prisma.promotion.findMany({
                where: {
                    storeId: req.storeId,
                    status: 'active',
                    startDate: { lte: now },
                    endDate: { gte: now },
                },
                orderBy: { createdAt: 'desc' },
            });
            const result = await Promise.all(promos.map(async (p) => {
                const productIds = (0, safeJson_1.safeJsonParse)(p.products, []);
                const products = productIds.length > 0 ? await prisma_1.prisma.product.findMany({
                    where: { id: { in: productIds }, storeId: req.storeId },
                    select: { id: true, name: true, price: true },
                }) : [];
                return {
                    ...p,
                    products: productIds,
                    productDetails: products,
                    discountValue: p.discount ?? 0,
                };
            }));
            return res.json(result);
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao buscar promocoes ativas' });
        }
    }
    async getById(req, res) {
        try {
            const promo = await prisma_1.prisma.promotion.findFirst({
                where: { id: req.params.id, storeId: req.storeId },
            });
            if (!promo)
                return res.status(404).json({ error: 'Promocao nao encontrada' });
            return res.json({ ...promo, products: (0, safeJson_1.safeJsonParse)(promo.products, []) });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao buscar promocao' });
        }
    }
    async create(req, res) {
        try {
            const data = promotionSchema.parse(req.body);
            const promo = await prisma_1.prisma.promotion.create({
                data: {
                    storeId: req.storeId,
                    title: data.title,
                    description: data.description ?? undefined,
                    discount: data.discount ?? undefined,
                    products: JSON.stringify(data.products || []),
                    conditions: data.conditions ?? undefined,
                    startDate: data.startDate ? new Date(data.startDate) : new Date(),
                    endDate: data.endDate ? new Date(data.endDate) : new Date(),
                    status: data.status || 'draft',
                },
            });
            return res.status(201).json({ ...promo, products: (0, safeJson_1.safeJsonParse)(promo.products, []) });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError)
                return res.status(400).json({ error: 'Dados invalidos', details: err.errors });
            console.error(err);
            return res.status(500).json({ error: 'Erro ao criar promocao' });
        }
    }
    async update(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.promotion.findFirst({ where: { id, storeId } });
            if (!existing)
                return res.status(404).json({ error: 'Promocao nao encontrada' });
            const data = promotionSchema.partial().parse(req.body);
            const updateData = {};
            if (data.title !== undefined)
                updateData.title = data.title;
            if (data.description !== undefined)
                updateData.description = data.description || null;
            if (data.discount !== undefined)
                updateData.discount = data.discount;
            if (data.products !== undefined)
                updateData.products = JSON.stringify(data.products);
            if (data.conditions !== undefined)
                updateData.conditions = data.conditions;
            if (data.startDate !== undefined)
                updateData.startDate = new Date(data.startDate);
            if (data.endDate !== undefined)
                updateData.endDate = new Date(data.endDate);
            if (data.status !== undefined)
                updateData.status = data.status;
            const promo = await prisma_1.prisma.promotion.update({ where: { id }, data: updateData });
            return res.json({ ...promo, products: (0, safeJson_1.safeJsonParse)(promo.products, []) });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError)
                return res.status(400).json({ error: 'Dados invalidos', details: err.errors });
            console.error(err);
            return res.status(500).json({ error: 'Erro ao atualizar promocao' });
        }
    }
    async activate(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.promotion.findFirst({ where: { id, storeId } });
            if (!existing)
                return res.status(404).json({ error: 'Promocao nao encontrada' });
            const promo = await prisma_1.prisma.promotion.update({ where: { id }, data: { status: 'active' } });
            return res.json({ ...promo, products: (0, safeJson_1.safeJsonParse)(promo.products, []) });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao ativar promocao' });
        }
    }
    async delete(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.promotion.findFirst({ where: { id, storeId } });
            if (!existing)
                return res.status(404).json({ error: 'Promocao nao encontrada' });
            await prisma_1.prisma.promotion.delete({ where: { id } });
            return res.json({ message: 'Promocao removida' });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao remover promocao' });
        }
    }
}
exports.PromotionController = PromotionController;
//# sourceMappingURL=PromotionController.js.map