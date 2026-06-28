"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProductController = void 0;
const prisma_1 = require("../lib/prisma");
const zod_1 = require("zod");
const safeJson_1 = require("../lib/safeJson");
const optimizer_1 = require("../lib/optimizer");
const productSchema = zod_1.z.object({
    name: zod_1.z.string().min(1).max(100),
    description: zod_1.z.string().optional(),
    price: zod_1.z.coerce.number().positive(),
    category: zod_1.z.string().max(50).optional(),
    specs: zod_1.z.string().optional(),
});
async function resolveCategory(storeId, categoryName) {
    if (!categoryName)
        return null;
    const name = optimizer_1.Optimizer.normalizeCategory(categoryName);
    if (!name)
        return null;
    const existing = await prisma_1.prisma.category.findUnique({
        where: { storeId_name: { storeId, name } },
    });
    if (!existing) {
        await prisma_1.prisma.category.create({ data: { storeId, name } }).catch(() => { });
    }
    return name;
}
class ProductController {
    async list(req, res) {
        try {
            const storeId = req.storeId;
            const products = await prisma_1.prisma.product.findMany({
                where: { storeId },
                orderBy: { createdAt: 'desc' },
            });
            return res.json(products.map(p => ({ ...p, photos: (0, safeJson_1.safeJsonParse)(p.photos, []), specs: (0, safeJson_1.safeJsonParse)(p.specs, {}) })));
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao listar produtos' });
        }
    }
    async getById(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const product = await prisma_1.prisma.product.findFirst({
                where: { id, storeId },
            });
            if (!product) {
                return res.status(404).json({ error: 'Produto não encontrado' });
            }
            return res.json({ ...product, photos: (0, safeJson_1.safeJsonParse)(product.photos, []), specs: (0, safeJson_1.safeJsonParse)(product.specs, {}) });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao buscar produto' });
        }
    }
    async create(req, res) {
        try {
            const data = productSchema.parse(req.body);
            const storeId = req.storeId;
            const files = req.files;
            const photos = files ? files.map(f => f.filename) : [];
            const category = await resolveCategory(storeId, data.category);
            const product = await prisma_1.prisma.product.create({
                data: {
                    storeId,
                    name: optimizer_1.Optimizer.normalizeName(data.name),
                    description: data.description?.trim() || null,
                    price: optimizer_1.Optimizer.formatPrice(data.price),
                    category,
                    photos: JSON.stringify(photos),
                    specs: data.specs || '{}',
                },
            });
            return res.status(201).json({ ...product, photos: (0, safeJson_1.safeJsonParse)(product.photos, []), specs: (0, safeJson_1.safeJsonParse)(product.specs, {}) });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao criar produto' });
        }
    }
    async update(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.product.findFirst({
                where: { id, storeId },
            });
            if (!existing) {
                return res.status(404).json({ error: 'Produto não encontrado' });
            }
            const data = productSchema.partial().parse(req.body);
            const files = req.files;
            const newPhotoNames = files && files.length > 0 ? files.map(f => f.filename) : [];
            const category = data.category !== undefined ? await resolveCategory(storeId, data.category) : undefined;
            let existingPhotos = [];
            const rawExisting = req.body?.existingPhotos;
            if (typeof rawExisting === 'string') {
                try {
                    existingPhotos = JSON.parse(rawExisting);
                }
                catch {
                    existingPhotos = [];
                }
            }
            else if (Array.isArray(rawExisting)) {
                existingPhotos = rawExisting;
            }
            const allPhotos = [...existingPhotos, ...newPhotoNames];
            const updateData = {};
            if (data.name !== undefined)
                updateData.name = optimizer_1.Optimizer.normalizeName(data.name);
            if (data.description !== undefined)
                updateData.description = data.description?.trim() || null;
            if (data.price !== undefined)
                updateData.price = optimizer_1.Optimizer.formatPrice(data.price);
            if (category !== undefined)
                updateData.category = category;
            if (data.specs !== undefined)
                updateData.specs = data.specs;
            updateData.photos = JSON.stringify(allPhotos);
            const product = await prisma_1.prisma.product.update({
                where: { id },
                data: updateData,
            });
            return res.json({ ...product, photos: (0, safeJson_1.safeJsonParse)(product.photos, []), specs: (0, safeJson_1.safeJsonParse)(product.specs, {}) });
        }
        catch (err) {
            if (err instanceof zod_1.z.ZodError) {
                return res.status(400).json({ error: 'Dados inválidos', details: err.errors });
            }
            console.error(err);
            return res.status(500).json({ error: 'Erro ao atualizar produto' });
        }
    }
    async delete(req, res) {
        try {
            const id = req.params.id;
            const storeId = req.storeId;
            const existing = await prisma_1.prisma.product.findFirst({
                where: { id, storeId },
            });
            if (!existing) {
                return res.status(404).json({ error: 'Produto não encontrado' });
            }
            await prisma_1.prisma.product.delete({ where: { id } });
            return res.json({ message: 'Produto removido' });
        }
        catch (err) {
            console.error(err);
            return res.status(500).json({ error: 'Erro ao remover produto' });
        }
    }
}
exports.ProductController = ProductController;
//# sourceMappingURL=ProductController.js.map