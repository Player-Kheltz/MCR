"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CategoryController = void 0;
const prisma_1 = require("../lib/prisma");
const zod_1 = require("zod");
const optimizer_1 = require("../lib/optimizer");
const categorySchema = zod_1.z.object({
    name: zod_1.z.string().min(1).max(50),
});
class CategoryController {
    async list(req, res) {
        try {
            const categories = await prisma_1.prisma.category.findMany({
                where: { storeId: req.storeId },
                orderBy: { name: 'asc' },
                select: { id: true, name: true, createdAt: true },
            });
            return res.json(categories);
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao listar categorias' });
        }
    }
    async create(req, res) {
        try {
            const data = categorySchema.parse(req.body);
            const name = optimizer_1.Optimizer.normalizeCategory(data.name);
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.category.findUnique({
                where: { storeId_name: { storeId, name } },
            });
            if (existing) {
                return res.status(409).json({ error: 'Categoria ja existe', category: existing });
            }
            const category = await prisma_1.prisma.category.create({
                data: { storeId, name },
            });
            return res.status(201).json(category);
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Nome invalido', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao criar categoria' });
        }
    }
    async delete(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const cat = await prisma_1.prisma.category.findFirst({ where: { id, storeId } });
            if (!cat)
                return res.status(404).json({ error: 'Categoria nao encontrada' });
            // Unlink from products (set category to null)
            await prisma_1.prisma.product.updateMany({
                where: { storeId, category: cat.name },
                data: { category: null },
            });
            await prisma_1.prisma.category.delete({ where: { id } });
            return res.json({ message: 'Categoria removida' });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao remover categoria' });
        }
    }
    async merge(req, res) {
        try {
            const { from, to } = req.body;
            if (!from || !to)
                return res.status(400).json({ error: 'Informe from e to' });
            const storeId = req.storeId;
            const toName = optimizer_1.Optimizer.normalizeCategory(to);
            // Ensure target exists
            const target = await prisma_1.prisma.category.findUnique({
                where: { storeId_name: { storeId, name: toName } },
            });
            if (!target) {
                await prisma_1.prisma.category.create({ data: { storeId, name: toName } });
            }
            // Move products
            await prisma_1.prisma.product.updateMany({
                where: { storeId, category: from },
                data: { category: toName },
            });
            // Delete source
            await prisma_1.prisma.category.deleteMany({
                where: { storeId, name: from },
            });
            return res.json({ message: 'Categorias mescladas', target: toName });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao mesclar' });
        }
    }
}
exports.CategoryController = CategoryController;
//# sourceMappingURL=CategoryController.js.map